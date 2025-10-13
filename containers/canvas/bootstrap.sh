#!/usr/bin/env bash
set -euo pipefail

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${THIS_DIR}"

ENV_FILE="${ENV_FILE:-.env}"
if [[ ! -f "${ENV_FILE}" ]]; then
  cp .env.example "${ENV_FILE}"
fi

# shellcheck source=/dev/null
source "${ENV_FILE}"

CANVAS_LMS_REF="${CANVAS_LMS_REF:-stable}"

if [[ ! -d canvas-lms/.git ]]; then
  git clone --depth 1 --branch "${CANVAS_LMS_REF}" https://github.com/instructure/canvas-lms.git canvas-lms
else
  git -C canvas-lms fetch --depth 1 origin "${CANVAS_LMS_REF}"
  git -C canvas-lms checkout "${CANVAS_LMS_REF}"
  git -C canvas-lms reset --hard "origin/${CANVAS_LMS_REF}"
fi

python3 - <<'PY'
import os
env_path = os.environ.get("ENV_FILE", ".env")
with open(env_path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()
if any(line.strip() == "ENCRYPTION_KEY=change-me" for line in lines):
    import secrets
    key = secrets.token_hex(64)
    with open(env_path, "w", encoding="utf-8") as fh:
        for line in lines:
            if line.strip() == "ENCRYPTION_KEY=change-me":
                fh.write(f"ENCRYPTION_KEY={key}\n")
            else:
                fh.write(line)
PY

mkdir -p canvas-lms/config
cp -n canvas-lms/docker-compose/config/*.yml canvas-lms/config/ 2>/dev/null || true
cat > canvas-lms/config/domain.yml <<'YAML'
production:
  domain: "localhost"

test:
  domain: localhost

development:
  domain: "localhost"
YAML

docker compose build

docker compose run --rm canvas-web bash -lc '
  set -e
  bundle config set without "production"
  bundle check || bundle install --jobs=${BUNDLE_JOBS:-4}
  yarn install --frozen-lockfile || yarn install
  bundle exec rake db:create
  bundle exec rake db:initial_setup
  bundle exec rake canvas:compile_assets_dev
'

docker compose run --rm canvas-web bash -lc '
  set -e
  bundle exec rails runner <<"RUBY"
    def ensure_user(email, password, full_name)
      account = Account.default
      pseudonym = Pseudonym.active.where(account: account, unique_id: email).first
      user = pseudonym&.user || User.create!(name: full_name, short_name: full_name.split.first, sortable_name: full_name)
      pseudonym ||= user.pseudonyms.build(account: account, unique_id: email)
      pseudonym.password = password
      pseudonym.password_confirmation = password
      pseudonym.save!
      user.communication_channels.find_or_create_by!(path: email) { |cc| cc.workflow_state = "active" }
      user.register!
      user
    end

    account = Account.default
    course = Course.find_or_initialize_by(course_code: "DEV101", root_account: account)
    if course.new_record?
      course.account = account
      course.name = "Canvas Sample Course"
      course.workflow_state = "claimed"
      course.start_at = Time.zone.now.beginning_of_day
      course.save!
      course.offer!
    end

    section = course.default_section || course.course_sections.create!(name: "Section 1")

    teacher = ensure_user(ENV.fetch("CANVAS_SAMPLE_TEACHER_EMAIL", "teacher@example.com"), ENV.fetch("CANVAS_SAMPLE_TEACHER_PASSWORD", "canvas-teacher-password"), "Taylor Teacher")
    teacher_enrollment = course.enroll_teacher(teacher, enrollment_state: "active", section: section)
    teacher_enrollment.accept!

    student = ensure_user(ENV.fetch("CANVAS_SAMPLE_STUDENT_EMAIL", "student@example.com"), ENV.fetch("CANVAS_SAMPLE_STUDENT_PASSWORD", "canvas-student-password"), "Sam Student")
    student_enrollment = course.enroll_student(student, enrollment_state: "active", section: section)
    student_enrollment.accept!

    group = course.assignment_groups.find_or_create_by!(name: "Assignments")
    assignment = course.assignments.find_or_initialize_by(name: "Welcome Assignment")
    if assignment.new_record?
      assignment.assignment_group = group
      assignment.submission_types = "online_text_entry"
      assignment.points_possible = 10
      assignment.due_at = 1.week.from_now
      assignment.save!
      assignment.publish!
    end

    module_record = course.context_modules.find_or_create_by!(name: "Getting Started")
    module_record.unpublish!
    module_record.publish!
    module_record.add_item({ id: assignment.id, type: "assignment" }) unless module_record.content_tags.exists?(content_id: assignment.id, content_type: "Assignment")

    puts "Sample course ready at DEV101"
  RUBY
'

docker compose up -d

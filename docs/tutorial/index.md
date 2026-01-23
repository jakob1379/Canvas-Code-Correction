---
title: Tutorial for Course Responsible
---

# Create Your First Work Package in 10 Minutes

Welcome, **course responsible and course administrators**. This tutorial guides
you through creating a **work package**: a self-contained unit that defines how
student assignments are automatically graded in Canvas Code Correction (CCC).

## What is a Work Package?

A **work package** includes everything needed to grade assignments for your
course:

1. **Grader Docker Image**: A container with your programming language, testing
   frameworks, and dependencies.
2. **Grader Test Scripts**: Code that evaluates student submissions and produces
   scores and feedback.

Once you create a work package, CCC platform operators can deploy it to
automatically grade submissions, upload feedback to Canvas, and post grades.

## Quick Overview: What You will Build

In this linear tutorial you will:

1. **Set up prerequisites** ([Prerequisites](./02-prerequisites.md)) – Canvas
   API access, Docker basics, Python 3.13+
2. **Create a grader Docker image**
   ([Creating Grader Docker Image](./03-creating-grader-image.md)) – Build a
   container with your testing environment
3. **Write grader tests** ([Writing Grader Tests](./04-writing-grader-tests.md))
   – Write scripts that evaluate student submissions
4. **Package everything** – Combine image and tests into a work package ready
   for deployment

Each step builds on the previous one. We will move from simplest example to
production‑ready work package.

## A Minimal Work Package

Here is the directory structure of a complete work package:

```bash
my‑work‑package/
├── Dockerfile                 # Builds the grader Docker image
├── grader/
│   ├── main.py               # Entry point for the grader
│   └── tests/                # Your grader test scripts
└── work‑package.yaml         # Metadata (name, version, etc.)
```

You will create each piece in the following pages.

## Let us Get Started!

First, ensure you have the prerequisites ready. Head to
[Prerequisites](./02-prerequisites.md) to check your setup.

!!! note "Platform Operators"
    Deploying and operating the CCC platform is handled by **platform operators**. After you create
    your work package, they will configure your course, set up scheduling, and monitor results. See
    the **Platform Setup** section for operator documentation.

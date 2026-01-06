---
title: Tutorial for Course Responsible
---

# Tutorial: Creating Work Packages for Canvas Code Correction

Welcome to the Canvas Code Correction (CCC) tutorial for **course responsible and course administrators**. This guide focuses on creating **work packages**—self-contained units that define how student assignments are automatically graded.

## What is a Work Package?

A **work package** includes everything needed to grade assignments for your course:

1. **Grader Docker Image**: A container with your programming language, testing frameworks, and dependencies
2. **Grader Test Scripts**: Code that evaluates student submissions and produces scores and feedback

Once you create a work package, the CCC platform operators can deploy it to automatically grade submissions, upload feedback to Canvas, and post grades.

## What You'll Learn in This Tutorial

- Setting up prerequisites (Canvas API access, Docker basics)
- Creating a grader Docker image with your testing environment
- Writing grader tests that evaluate student submissions

## What's Not Covered Here

Deploying and operating the CCC platform is handled by **platform operators**. After you create your work package, they will:

- Configure your course on the CCC platform
- Set up Prefect for scheduling corrections
- Monitor results and handle infrastructure

See the **Platform Setup** section for operator documentation.

## Let's Get Started!

First, ensure you have the prerequisites ready.
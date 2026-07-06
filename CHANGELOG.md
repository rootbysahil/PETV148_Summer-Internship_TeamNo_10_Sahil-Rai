# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-04

### Added
- Layered architectural code implementation separating core logic, engines, UI layout screens, and reports.
- Centralized configuration parameters using Pydantic Settings supporting `.env` loads.
- Async scanning engine checks using `httpx` and token-bucket based rate limiter.
- Curated platforms signature list config file containing status/message inspection mappings.
- Custom strategy-based Exporters generating JSON, CSV, TXT, and Jinja2-rendered HTML reports.
- Comprehensive test suite for input validation, configuration, reports, and scanner logic.

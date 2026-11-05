# TinyIntent

## Overview

TinyIntent is an offline intent classification system designed to explore Edge AI on resource-constrained embedded devices. It classifies textual commands locally on an ESP32-S3 and aims to reject commands that fall outside its supported intents.

In later versions, TinyIntent will explore lightweight on-device personalisation, allowing the system to adapt to user corrections without retraining the complete neural network.

## Motivation

Running intent classification locally can reduce inference latency, preserve data privacy, and allow the system to continue operating without an internet connection.

These advantages come with significant constraints compared with cloud-based inference. The ESP32-S3 provides limited memory, storage, and computational resources, requiring careful consideration of model size, inference latency, memory usage, and accuracy.

TinyIntent uses these constraints as part of the engineering challenge rather than treating them only as limitations.

## Hardware

- LILYGO T-QT Pro
- ESP32-S3 MCU
- No external sensors or peripherals required

Hardware resources such as available flash, RAM, and PSRAM will be measured on the target device during platform bring-up rather than assumed from specifications.

## Current Status

**Current milestone:** v0.1 - Embedded Platform Bring-up

**ML functionality:** Not implemented

The current focus is establishing a reliable and reproducible embedded firmware foundation before introducing machine-learning components.

## Roadmap

| Version | Milestone |
|---|---|
| v0.1 | Embedded platform bring-up |
| v0.2 | Dataset and classical ML baseline |
| v0.3 | Tiny neural intent classifier |
| v0.4 | First embedded inference |
| v0.5 | INT8 quantisation and PC/MCU inference parity |
| v0.6 | Unknown / out-of-distribution command rejection |
| v0.7 | On-device personalisation |
| v0.8 | Persistence and robustness |
| v0.9 | Embedded optimisation and benchmarking |
| v1.0 | Portfolio-ready release |

## Building

Build instructions will be added during the v0.1 embedded platform bring-up.

## License

License selection is pending.


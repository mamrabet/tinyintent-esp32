# TinyIntent Architecture

## Purpose

This document will cover the architecture and component responsibilities of the TinyIntent project. v0.1 focuses on the embedded platform bring-up. ML inference/personalisation is not implemented yet.

## Current Architecture

Application
    │
    │ uses
    ▼
┌───────────────────────────────┐
│ Display | Buttons | Diagnostics│
└───────────────────────────────┘
    │
    │ uses
    ▼
ESP-IDF
    │
    │ controls/accesses
    ▼
ESP32-S3 / T-QT Pro hardware

The Application determines the system behavior in response to events. Platform components encapsulate board- and framework-specific functionality required by the application.

## Components

### Application

The application is responsible for:

- Handling/interpreting user events and switching system states accordingly
- Coordination between system components

The application is NOT responsible for:

- Hardware specific configuration (GPIO/ SPI configuration, etc ...)
- Hardware logic (button debouncing / the way text is displayed)
- Calling low-level hardware APIs

### Display

The display component is responsible for:

- Initialisation and configuration of the display
- Formatting and rendering requested information

The display component is NOT responsible for:

- Application state transitions and handling user events
- ML classification
- Collecting diagnostic data

### Buttons

The Buttons component is responsible for:

- Configuring the GPIOs associated with the physical buttons
- Reading the physical button states
- Handling button debouncing
- Translating physical button state changes into logical events such as `BUTTON_A_PRESSED`

The Buttons component is NOT responsible for:

- Deciding what a button press means to the application
- Changing the application state
- Triggering display changes directly
- Implementing application-specific behavior

### Diagnostics

The Diagnostics component is responsible for:

- Retrieving runtime system information through ESP-IDF
- Providing hardware and memory information to the Application
- Providing firmware and system information in a hardware-independent representation where practical

Examples of diagnostic information include:

- Available heap memory
- Minimum free heap memory
- Flash information
- PSRAM information
- ESP32 chip information
- Firmware version

The Diagnostics component is NOT responsible for:

- Deciding when diagnostic information should be requested
- Formatting diagnostic information for the TFT
- Changing the application state
- Interacting directly with user input

## Dependency Direction

Application
|
v
Display | Buttons | Diagnostics
|
v
ESP-IDF
|
v
ESP32-S3 / T-QT Pro

The Application coordinates system behavior. Platform components isolate
hardware-specific functionality and access ESP-IDF when required.


## Design Principles

- Keep application logic separate from hardware-specific code.
- Give each component one clear responsibility.
- Platform components should not directly control each other.
- Add abstractions only when they solve a concrete problem.


## Future Architecture

Not part of v0.1.

Future releases are expected to introduce components for:

- text preprocessing
- ML inference
- unknown-command detection
- personalisation
- persistent storage

These components are intentionally not designed in detail yet.


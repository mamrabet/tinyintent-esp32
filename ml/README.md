# TinyIntent ML

This directory contains the host-side machine-learning pipeline for TinyIntent.

The ML pipeline is developed and evaluated on the host before models are
deployed to the ESP32-S3.

## Current Milestone

**v0.2 - Dataset and Classical ML Baseline**

Current goals:

- Define the intent taxonomy
- Build and validate the initial dataset
- Establish a classical ML baseline
- Define reproducible evaluation metrics

Neural-network training and embedded inference are not part of this milestone.

## Intent Taxonomy

TinyIntent currently supports five intents:

| Intent | Description |
|---|---|
| `SYSTEM_CONTROL` | Control the overall device operating state |
| `SYSTEM_STATUS` | Query current device or system information |
| `NETWORK_CONTROL` | Control network and connectivity behavior |
| `DIAGNOSTICS` | Request diagnostic or health-check operations |
| `HELP` | Query supported commands and capabilities |

Unsupported commands are maintained separately for future UNKNOWN/OOD
rejection experiments.

## Dataset

The initial dataset is stored under:

data/
├── train.json
├── validation.json
├── test.json
└── unknown.json

Current dataset size:

| Split | Examples |
|---|---:|
| Training | 40 |
| Validation | 10 |
| Test | 10 |
| Unknown/OOD | 10 |

The dataset is intentionally small during v0.2. Its primary purpose is to
validate the taxonomy, preprocessing pipeline, evaluation methodology, and
baseline classifier.

## UNKNOWN / OOD Strategy

`UNKNOWN` is not currently treated as a normal training class.

Instead, unsupported commands are kept separately so later versions can
investigate whether the classifier can reject inputs that fall outside its
supported intent distribution.

## Planned Pipeline

Dataset
|
v
Validation
|
v
Text preprocessing
|
v
Classical ML baseline
|
v
Evaluation
|
v
Tiny neural classifier
|
v
Quantisation
|
v
ESP32-S3 inference


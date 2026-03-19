# Armenian Duduk in Trove

This repository contains a dataset of **metadata records related to Armenian duduk music** collected from **Trove (National Library of Australia)**.

The dataset was prepared for **Open Data Armenia** as part of its broader effort to identify, document, and preserve Armenian cultural heritage across international archives, libraries, and digital collections.

## Repository Description

Metadata dataset of Armenian duduk-related music records collected from Trove (National Library of Australia) for Open Data Armenia.

## Data Source

**Source:** Trove (National Library of Australia)  
**Platform:** https://trove.nla.gov.au

Trove is the discovery platform of the National Library of Australia and provides access to records from Australian libraries, archives, museums, and other partner institutions.

This repository focuses on records from the **music** category in Trove, using the query **"armenian duduk"**.

## Dataset Contents

The dataset contains **metadata only**.  
It does **not** reproduce original recordings, scores, or protected source materials.

Each row may include:

- title
- date or period
- author or creator
- description or abstract
- URL to original object
- Trove ID
- Trove URL

## Main Data File

`data/trove_armenian_duduk.csv`

## Methodology

The dataset was collected through the Trove API using keyword-based search in the **music** category.

The extraction workflow includes:

- API-based collection
- pagination through Trove results
- metadata normalization
- cleaning of nested fields
- export to CSV and JSONL

## Suggested Use Cases

This dataset may support research in:

- Armenian music history
- Armenian cultural heritage
- duduk performance and recording history
- digital humanities
- archival discovery
- diaspora studies

## Project Context

This dataset was created for **Open Data Armenia** in order to support the documentation of Armenian cultural heritage represented in global digital collections.

## Data Rights and Attribution

This repository contains **metadata only** collected from Trove.

Please see [DATA_RIGHTS.md](DATA_RIGHTS.md) for the attribution and rights statement.

## Maintainer

Prepared for **Open Data Armenia**.

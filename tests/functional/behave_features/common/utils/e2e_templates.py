# -*- coding: utf-8 -*-
"""String templates to be used for generating various files throughout E2E testing."""

# The base OWNERS file string template.
base_owners_file: str = """\
chart:
  name: ${chart_name}
  shortDescription: Test chart for testing chart submission workflows.
publicPgpKey: ${public_key}
providerDelivery: ${provider_delivery}
users:
- githubUsername: ${bot_name}
vendor:
  label: ${vendor}
  name: ${vendor_pretty}
"""

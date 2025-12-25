

Investigate why he reversed x and z


Implement center offset calculation

Script to automatically extract, create assetbrowser, diff, report, zip them, items

Move the code for building calculation from building-sizes.py into parsing/core. Make it accessible through a property "building_size" on Asset. The computed value should be cached. Check the correctness of the implementation by running
  tests/integration/verify_building_sizes.py::test_building_size_parsing_errors 
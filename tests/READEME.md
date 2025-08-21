## Testing Process

1. Run any unit tests using the command:
   ```bash
   python -m unittest discover -s tests
   ```
1, create a snap show of production files with snapshot.bash scrip
2. Run the following command to copy test files from the external test files snapshot:
   ```bash
   bash snapshot.bash
   ```
2. run script to copy test files from external test files snapshot
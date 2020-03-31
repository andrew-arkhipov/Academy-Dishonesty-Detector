# Academic Dishonesty Detector
Online cheating detector to be used for UT OnRamps' Precalculus Course

<br>

### Virtual Environment

It is highly recommended to use a Python virtual environment when running this script. Run the following commands in the root directory of the project.
```
python3 -m venv <env-folder-name>
```

To activate that virtual environment, use the below command:
```
source <env-folder-name>/bin/activate
```

After activating, to install the dependencies run
```
pip3 install -r requirements.txt
```

### File Structure
`names.txt` will be created and will contain the names of those who were determined to have cheated by a rudimentary detection algorithm.

`credentials.json` should include your personal information for logging into UT's Canvas system.

`selenium_scraper.py` is the actual script. To run it, use the below command:
```
python selenium_scraper.py
```


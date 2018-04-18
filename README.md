## Synopsis
This is a companion app to my Overwatch Team Buildling website: https://overwatch.johnelgin.me
The app currently takes screenshots of your primary display, analyzes them to see what map you're on and heroes are selected for both teams, and shares it in near real-time to the website for you and your team to use.

## Installation
Until I do further testing, install this environment using Conda (Python 3.6 version), available at: 
https://www.anaconda.com/download/#windows

After installation, you can create a new environment with the required dependencies using:

1. Open command prompt and navigate to this app's directory (overwatch-python or otherwise)
2. Create a conda environment using `conda env create -f conda_environment.yml`
3. Activate the new environment: `activate OverwatchApp`
4. Start the app: `pythonw overwatch_app.py`

After the initial setup, you only need to do steps 1,3, and 4

## Contributors
I'm currently tracking issues here in GitHub. I encourage feature suggestions as well as code improvement!

## License
Apache License 2.0 per LICENSE.txt

Also any reference to Overwatch including images are covered under their Copyright notice:

®2016 Blizzard Entertainment, Inc. All rights reserved. Overwatch is a trademark or registered trademark of Blizzard Entertainment, Inc. in the U.S. and/or other countries.


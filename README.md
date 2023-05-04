# Front-end CO2

This is a script to gather data on CPU and RAM energy usage associated with different file types and sizes used in delivery and rendering of a web page. 

The goal is that this information can be used to refine the estimates provided by web page carbon calculators that currently only look at total page size (not actual measured resource usage as provided by some more sophisticated testing tools).

## Methodology

The following approach is used to identify the energy usage associated with different file types (using MIME type/subtype) on the web.

Using a list of the popular domains the following process is followed:
1. Visit the domain normally and capture a list of all URLs with their associated file types and sizes
1. Visit the domain normally a set number of iterations and record the energy usage baseline and run time
1. Then, for each MIME type:
    1. Visit the domain a set number of iterations and record energy usage - but blocking all requests that would return the current MIME type
    1. Calculate the energy usage difference between the baseline and the blocked requests - i.e. the energy usage associated with the current MIME type
1. The energy usage difference and run time is then divided by the number of iterations to get a normalized value per page load (for comparison across different iteration counts)
1. The output is then written to a CSV file - you can see an example in the [data](data) directory

The script is written in Python and uses the [Playwright](https://playwright.dev/) browser automation library to drive the browser and block requests. It also uses the [Intel Power Gadget](https://software.intel.com/content/www/us/en/develop/articles/intel-power-gadget.html) to measure the energy usage of the CPU and RAM.

## Limitations

This approach has a number of limitations that users should be aware of:
* It only looks at the energy usage of the CPU and RAM - not the GPU, network or disk - those should be modelled via other means
* Different network, hardware, operating system, browser and browser settings will all affect the energy usage
* The energy usage is only measured for the initial page load - not for any subsequent interactions
* Only the homepages of the most popular domains have been checked this far - so may not be representative of the web as a whole
* Some portion of MIME types will implicitly be blocked by blocking other MIME types - e.g. blocking CSS and JS files may cause some images to be not be loaded
* Blocking some MIME types may cause some pages to not load at all - e.g. blocking JS on a React site
* Since we are measuring CPU and RAM energy usage for the entire system (not just the browser) - while this is more accurate in some ways (it includes CPU effort associated with OS/kernel download/rendering activities) it also introduces more opportunities for noise in the measurements (e.g background tasks)

Some of these can be mitigated by running the script on a dedicated machine with a clean OS install and no other applications running, as well as testing on a decent number of domains with a large number of iterations to limit the affect of these artifacts.

Other limitations could be mitigated by testing on different machines to gather a broader data set, or through different testing approaches: e.g. gathering data from real users with a browser extension, or running lab tests with power logging devices.

## Requirements & Installation

Because there is not a cross platform energy usage API, this script currently only works on OS X and Windows (the latter still needs testing).

The script currently has minimal error checking or user guidance, so expect to do some troubleshooting or debugging if you run into issues.

To get started:

* [Install Intel Power Gadget](https://www.intel.com/content/www/us/en/developer/articles/tool/power-gadget.html)
* [Install Git](https://git-scm.com/downloads)
* [Install Python 3.10](https://python.org) or higher (note: for OS X it is recommended to use Homebrew as the standard Python distribution doesn't work with Poetry)
* [Install Poetry](https://python-poetry.org/docs/#installation) - remember to add it to your PATH if needed
* Clone this repository: `https://github.com/grugnog/frontend-co2.git`
* Switch directory: `cd frontend-co2`
* Install python dependencies: `poetry install`
* Install test browser: `poetry run playwright install chromium`
* Run the script: `poetry run python src/main.py`

Optionally:
* Pass in the number of iterations to run (default is 100): `poetry run python src/main.py 100`
* Adjust the set of domains to test by editing `data/domains.csv`

A full run with default settings will take 1-3 days, depending on the system and network etc.
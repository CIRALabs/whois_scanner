# Basic operation
1. Query list of domain (will be only gTLDs) via WHOIS to retrieve ‘country of registrant’ field. 
1. Flag any domain containing specific terms (e.g., ‘redacted for privacy’, ‘proxy’, ‘registration private’).
1. Tool should be able to handle a few hundred thousand domains efficiently (ideally not taking days per run) and have some basic logs for debugging.
1. Use any language you prefer, as long as the code is easy to run.
1. This project could be collaborative if more than one member wants to get involved. 

# Why we need this
We would like to isolate gTLD domains by country so we can run them through our crawler to capture usage data.  This is handy to give more context to the market share data. For example, if we know that % of domains under [ccTLD] are developed, parked etc, what are the equivalent rates for the gTLDs in the respective ccTLDs’ country.

# How to run
## Data definition
First you need to provide an input for the data to be processed.
The data should conform to the [JSON schema](./input.schema.json):

Script accepts two arguments: `pagenum` (starts at 0) and `pagesize`. If these are not provided, then the whole list will be processed.

## Localhost
Before you can run the program, you should create a virtual environment for the python executable
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then, you can run the program
```bash
python main.py
```

## Docker
```bash
docker build -t whois_scanner:latest .
docker run -it whois_scanner:latest
```

## Exit codes
The program has been written to split return codes into three categories:
* Negative value: The program failed and halted execution
* Zero value: The program succeeded
* Positive value: The program had errors, but did not halt execution. The number returned is the number of errors encountered.

## Logging
By default, the program is set to use ERROR only logging levels. However this can be controlled with the `LOGLEVEL` environment variable. It will accept the following values:
* DEBUG
* INFO
* WARN
* ERROR

An example of how to set the logging level:
```bash
LOGLEVEL=INFO python main.py
```

# Paging
By default the program will execute across the entire input list sequentially. This may not be desirable if the list is large as it will take a long time. Instead the program has been designed to be run with multiple executions in parallel. Each execution will read the entire input list, but will only operate on a specific subset of that list, as defined by command-line arguments.

## Paging locally
The `main.py` script accepts two ordered arguments `pagenum` and `pagesize`. When these arguments are provided, the program will only process `pagesize` domains, and will start with element number `pagesize * pagenum`.

The example below will process two sets of two domains (indexes 0 and 1, then 2 and 3):
```bash
python main.py 0 2
python main.py 1 2
```

We've also included a bash script to help run multiple executions. This script takes a single argument of `pagesize` and will parse the input file to determine how many pages need to be executed.

The example below, assuming a input list of 4 elements, will process two pages. The first will process indexes [0, 1, 2] and the second will process index 3.
```bash
bash run_local_parallel.sh 3
```

At the end of the execution, it will output the # of domains that were considered 'invalid' based on the exit codes returned.

## Paging with Docker
Similar to the local python execution, you can provide the `pagenum` and `pagesize` arguments to the docker script. The same logic will apply as above in determining which domains will be processed by the docker container.

```bash
docker build -t whois_scanner:latest .
docker run -it whois_scanner:latest 0 2
docker run -it whois_scanner:latest 1 2
```

A similar bash script is also provided to run multiple docker images in a paging scenario. This script will automatically build & run the docker containers:
*TODO: This currently still runs in sequence. It should be updated to run in parallel*
```bash
bash run_docker_paged.sh 3
```

Similar to the local execution, after completion, it will output the # of domains that were considered 'invalid' based on the exit codes returned.

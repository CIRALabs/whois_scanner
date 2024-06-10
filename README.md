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
python main.py <pagenum> <pagesize>
```

Or as a paged loop:
```bash
bash run_local_paged.sh 100
```


## Docker
<em>TODO: This is still in the works, as the input.json file has to be embedded into the docker container.</em>
```bash
docker build -t whois-crawler:latest .
docker run -it whois-crawler:latest <pagenum> <pagesize>
```

## Exit codes
The program has been written to split return codes into three categories:
* Negative value: The program failed and halted execution
* Zero value: The program succeeded
* Positive value: The program had errors, but did not halt execution. The number returned is the number of errors encountered.

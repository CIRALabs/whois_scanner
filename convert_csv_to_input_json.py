'''Simple script to convert a CSV file into the expected input.json'''

import csv
import json


def main():
    '''Runs the program'''
    with open("input.csv", encoding="UTF-8") as f, \
         open("input.json", encoding="UTF-8") as example:
        result = json.load(example)
        data = csv.DictReader(f)
        result["domains"] = []
        for row in data:
            url = row['input_url']
            result["domains"].append({"hostname": url})
    with open("input.json", "w", encoding="UTF-8") as output:
        output.write(json.dumps(result))


if __name__ == "__main__":
    main()

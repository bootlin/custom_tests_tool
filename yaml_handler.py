import os
import ruamel.yaml
import collections

class YAMLHandler:
    def get_job_from_yaml_file(file):
        with open(file) as f:
            job = ruamel.yaml.load(f, Loader=ruamel.yaml.RoundTripLoader)
            return job
            job['actions'][0]['deploy']['timeout']['minutes'] = 4000
            print(ruamel.yaml.dump(job, Dumper=ruamel.yaml.RoundTripDumper))


    def save_job_to_yaml_file(job, file):
        with open(file, 'w') as f:
            f.write(ruamel.yaml.dump(job, Dumper=ruamel.yaml.RoundTripDumper))


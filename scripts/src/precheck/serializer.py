"""Contains the logic to serialize / deserialize a Submission object to / from JSON.

A pair of custom JSONEncoder / JSONDecoder is required due to the fact that the Submission class
contains nested classes.

"""

import copy
import json

from precheck import submission


class SubmissionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, submission.Submission):
            obj_dict = copy.deepcopy(obj.__dict__)
            obj_dict["chart"] = obj_dict["chart"].__dict__
            obj_dict["report"] = obj_dict["report"].__dict__
            obj_dict["source"] = obj_dict["source"].__dict__
            obj_dict["tarball"] = obj_dict["tarball"].__dict__
            return obj_dict

        return json.JSONEncoder.default(self, obj)


class SubmissionDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        if "chart" in dct:
            chart_obj = submission.Chart(**dct["chart"])
            report_obj = submission.Report(**dct["report"])
            source_obj = submission.Source(**dct["source"])
            tarball_obj = submission.Tarball(**dct["tarball"])

            to_merge_dct = {
                "chart": chart_obj,
                "report": report_obj,
                "source": source_obj,
                "tarball": tarball_obj,
            }

            new_dct = dct | to_merge_dct
            return submission.Submission(**new_dct)
        return dct

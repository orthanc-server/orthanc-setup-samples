import os
from orthanc_api_client import OrthancApiClient, InstancesSet
import boto3
import dataclasses
import tempfile
import re


@dataclasses.dataclass
class S3Configuration:
     aws_access_key_id: str
     aws_secret_access_key: str
     bucket: str
     endpoint: str


class S3StudyExporter:

    def __init__(self, orthanc_api: OrthancApiClient, s3_config: S3Configuration, path_template: str, delete_after_export: bool) -> None:
        self.orthanc_api = orthanc_api
        self.s3_config = s3_config
        self.path_template = path_template
        self.delete_after_export = delete_after_export

    def generate_path(self, instances_set: InstancesSet) -> str:
        tags = self.orthanc_api.instances.get_tags(instances_set.instances_ids[0])

        path = self.path_template
        # e.g: path is "{StudyDate}/{PatientID}-{PatientName}.zip"
        for tag in re.findall(r"\{[a-zA-Z]+\}", path):                                  # e.g: tag is "{StudyDate}""
            tag_name = tag.replace("{", "").replace("}", "")                            # e.g: tag_name is "StudyDate"
            if tags.get(tag_name):
                path = path.replace(tag, tags.get(tag_name))
            elif tag_name == "OrthancStudyID":
                path = path.replace(tag, instances_set.study_id)
            elif tag_name == "InstancesSetID":
                path = path.replace(tag, instances_set.id)
            else:
                path = path.replace(tag, f"Unknown_{tag_name}")

        return path

    def export(self, study_id: str) -> bool:
        s3 = boto3.client('s3',
                          aws_access_key_id=self.s3_config.aws_access_key_id,
                          aws_secret_access_key=self.s3_config.aws_secret_access_key,
                          endpoint_url=self.s3_config.endpoint
                          )

        # take a snapshot of the study in its current state in case new instances are received while processing
        instances_set = InstancesSet.from_study(api_client=self.orthanc_api,
                                                study_id=study_id)

        with tempfile.NamedTemporaryFile() as file:
            instances_set.download_archive(file.name)

            s3.upload_file(Filename=file.name, 
                           Bucket=self.s3_config.bucket,
                           Key=self.generate_path(instances_set))

        if self.delete_after_export:
            instances_set.delete()


# test code to debug outside of Orthanc
if __name__ == "__main__":
    orthanc_api = OrthancApiClient(orthanc_root_url="http://192.168.0.10:8042")

    s3_config = S3Configuration(aws_access_key_id="minio",
                                aws_secret_access_key="miniopwd",
                                bucket="test-bucket",
                                endpoint="http://localhost:9000")

    study_exporter = S3StudyExporter(orthanc_api=orthanc_api,
                                     s3_config=s3_config,
                                     path_template="{PatientID}-{PatientName}-{PatientBirthDate}/{StudyDate}-{StudyDescription}.zip")

    study_exporter.export(study_id="15784736-a81865de-5c6fb131-4286a992-ec152f3b")




    # s3_region = get_secret("AWS_ACCESS_KEY")
    # aws_access_key = get_secret("AWS_ACCESS_KEY")
    # aws_secret_key = get_secret("AWS_SECRET_KEY")



    #         S3_REGION: "eu-west-1"
    #         AWS_ACCESS_KEY: "minio"
    #         AWS_SECRET_KEY: "miniopwd"
    #         S3_ENDPOINT: "http://minio:9000"
    #         S3_VIRTUAL_ADDRESSING: "false"
    #         S3_FILENAME_TEMPLATE: "$StudyDate$/$PatientID$-$PatientName$.zip" 
    #         S3_ORTHANC_USER: "python-script-user"
    #         S3_ORTHANC_PWD: "change-me"


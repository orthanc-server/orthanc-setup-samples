import importlib.util
import json
import pathlib
import sys
import types
import unittest


SCRIPT = pathlib.Path(__file__).with_name('compress_us_to_lossy.py')
JPEG_BASELINE = '1.2.840.10008.1.2.4.50'


class FakeDicom:
    def __init__(self, tags, frames=10, transfer_syntax='1.2.840.10008.1.2.1', data=b'compressed'):
        self.tags = tags
        self.frames = frames
        self.transfer_syntax = transfer_syntax
        self.data = data

    def GetInstanceSimplifiedJson(self):
        return json.dumps(self.tags)

    def GetInstanceFramesCount(self):
        return self.frames

    def GetInstanceTransferSyntaxUid(self):
        return self.transfer_syntax

    def SerializeDicomInstance(self):
        return self.data


class FakeReceivedInstanceAction:
    KEEP_AS_IS = 1
    MODIFY = 2


class FakeOrthanc(types.ModuleType):
    def __init__(self, source, transcoded=None, transcode_error=None, configuration=None):
        super().__init__('orthanc')
        self.ReceivedInstanceAction = FakeReceivedInstanceAction
        self.source = source
        self.transcoded = transcoded
        self.transcode_error = transcode_error
        self.configuration = configuration or {'DicomLossyTranscodingQuality': 70}
        self.transcode_calls = []
        self.errors = []
        self.callback = None

    def RegisterReceivedInstanceCallback(self, callback):
        self.callback = callback

    def GetConfiguration(self):
        return json.dumps(self.configuration)

    def CreateDicomInstance(self, received):
        return self.source

    def TranscodeDicomInstance(self, received, transfer_syntax):
        self.transcode_calls.append((received, transfer_syntax))
        if self.transcode_error:
            raise self.transcode_error
        return self.transcoded

    def LogInfo(self, message):
        pass

    def LogError(self, message):
        self.errors.append(message)


def LoadScript(fake_orthanc):
    sys.modules['orthanc'] = fake_orthanc
    spec = importlib.util.spec_from_file_location('compress_us_to_lossy', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def Tags(modality='US', lossy=None, sop_instance_uid='instance'):
    tags = {
        'Modality': modality,
        'PatientID': 'patient',
        'StudyInstanceUID': 'study',
        'SeriesInstanceUID': 'series',
        'SOPInstanceUID': sop_instance_uid,
    }
    if lossy is not None:
        tags['LossyImageCompression'] = lossy
    return tags


class CompressUsToLossyTests(unittest.TestCase):
    def test_modifies_multiframe_ultrasound_before_storage(self):
        source = FakeDicom(Tags())
        transcoded = FakeDicom(
            Tags(lossy='01', sop_instance_uid='lossy-instance'),
            transfer_syntax=JPEG_BASELINE,
            data=b'lossy',
        )
        orthanc = FakeOrthanc(source, transcoded)
        module = LoadScript(orthanc)

        action, data = module.ReceivedInstanceCallback(b'original', None)

        self.assertEqual(FakeReceivedInstanceAction.MODIFY, action)
        self.assertEqual(b'lossy', data)
        self.assertEqual([(b'original', JPEG_BASELINE)], orthanc.transcode_calls)

    def test_leaves_non_ultrasound_unchanged(self):
        orthanc = FakeOrthanc(FakeDicom(Tags(modality='DX')))
        module = LoadScript(orthanc)

        action, data = module.ReceivedInstanceCallback(b'original', None)

        self.assertEqual((FakeReceivedInstanceAction.KEEP_AS_IS, None), (action, data))
        self.assertEqual([], orthanc.transcode_calls)

    def test_leaves_single_frame_ultrasound_unchanged(self):
        orthanc = FakeOrthanc(FakeDicom(Tags(), frames=1))
        module = LoadScript(orthanc)

        action, data = module.ReceivedInstanceCallback(b'original', None)

        self.assertEqual((FakeReceivedInstanceAction.KEEP_AS_IS, None), (action, data))
        self.assertEqual([], orthanc.transcode_calls)

    def test_does_not_recompress_lossy_ultrasound(self):
        source = FakeDicom(Tags(lossy='01'), transfer_syntax=JPEG_BASELINE)
        orthanc = FakeOrthanc(source)
        module = LoadScript(orthanc)

        action, data = module.ReceivedInstanceCallback(b'original', None)

        self.assertEqual((FakeReceivedInstanceAction.KEEP_AS_IS, None), (action, data))
        self.assertEqual([], orthanc.transcode_calls)

    def test_keeps_original_when_transcoding_fails(self):
        orthanc = FakeOrthanc(FakeDicom(Tags()), transcode_error=RuntimeError('failed'))
        module = LoadScript(orthanc)

        action, data = module.ReceivedInstanceCallback(b'original', None)

        self.assertEqual((FakeReceivedInstanceAction.KEEP_AS_IS, None), (action, data))
        self.assertIn('failed', orthanc.errors[0])

    def test_keeps_original_when_identity_changes(self):
        source = FakeDicom(Tags())
        changed = Tags(lossy='01', sop_instance_uid='lossy-instance')
        changed['StudyInstanceUID'] = 'other-study'
        transcoded = FakeDicom(changed, transfer_syntax=JPEG_BASELINE)
        orthanc = FakeOrthanc(source, transcoded)
        module = LoadScript(orthanc)

        action, data = module.ReceivedInstanceCallback(b'original', None)

        self.assertEqual((FakeReceivedInstanceAction.KEEP_AS_IS, None), (action, data))
        self.assertIn('StudyInstanceUID changed', orthanc.errors[0])

    def test_keeps_original_when_lossy_metadata_is_missing(self):
        source = FakeDicom(Tags())
        transcoded = FakeDicom(
            Tags(sop_instance_uid='lossy-instance'),
            transfer_syntax=JPEG_BASELINE,
        )
        orthanc = FakeOrthanc(source, transcoded)
        module = LoadScript(orthanc)

        action, data = module.ReceivedInstanceCallback(b'original', None)

        self.assertEqual((FakeReceivedInstanceAction.KEEP_AS_IS, None), (action, data))
        self.assertIn('lossy compression metadata is missing', orthanc.errors[0])

    def test_keeps_original_when_lossy_transcode_reuses_sop_uid(self):
        source = FakeDicom(Tags())
        transcoded = FakeDicom(Tags(lossy='01'), transfer_syntax=JPEG_BASELINE)
        orthanc = FakeOrthanc(source, transcoded)
        module = LoadScript(orthanc)

        action, data = module.ReceivedInstanceCallback(b'original', None)

        self.assertEqual((FakeReceivedInstanceAction.KEEP_AS_IS, None), (action, data))
        self.assertIn('SOPInstanceUID did not change', orthanc.errors[0])

    def test_rejects_unexpected_lossy_quality_at_startup(self):
        orthanc = FakeOrthanc(
            FakeDicom(Tags()),
            configuration={'DicomLossyTranscodingQuality': 90},
        )

        LoadScript(orthanc)

        self.assertIsNone(orthanc.callback)
        self.assertIn('must be 70', orthanc.errors[0])

    def test_rejects_ingest_retranscoding_at_startup(self):
        orthanc = FakeOrthanc(
            FakeDicom(Tags()),
            configuration={
                'DicomLossyTranscodingQuality': 70,
                'IngestTranscoding': '1.2.840.10008.1.2.4.70',
                'IngestTranscodingOfCompressed': True,
            },
        )

        LoadScript(orthanc)

        self.assertIsNone(orthanc.callback)
        self.assertIn('must be false', orthanc.errors[0])


if __name__ == '__main__':
    unittest.main()

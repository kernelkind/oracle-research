import unittest

from calibration_package import freeze_create_result, freeze_instance_record, sanitize_instance_list

class CalibrationPackageTest(unittest.TestCase):


    def test_instance_record_binds_the_create_result_and_discards_secrets(self):
        create_result = {"success": True, "new_contract": 88001234}
        raw = {
            "instances": {
                "id": 88001234,
                "machine_id": 21555,
                "bundle_id": 1075358098,
                "actual_status": "running",
                "intended_status": "running",
                "image_uuid": "kernelkind/oracle-mvp@sha256:" + "4" * 64,
                "gpu_name": "RTX PRO 6000 WS",
                "num_gpus": 1,
                "disk_space": 200.0,
                "dph_total": 1.64,
                "is_bid": False,
                "verification": "verified",
                "label": "crec-72-gte-full-build",
                "jupyter_token": "must-not-survive",
            }
        }

        record = freeze_instance_record(create_result, raw)
        self.assertEqual(record["id"], 88001234)
        self.assertEqual(record["label"], "crec-72-gte-full-build")
        self.assertNotIn("jupyter_token", record)

        create_result["new_contract"] = 99999
        with self.assertRaisesRegex(ValueError, "create result"):
            freeze_instance_record(create_result, raw)

    def test_instance_inventory_discards_credentials_and_connection_data(self):
        raw = {
            "instances": [
                {
                    "id": 88001234,
                    "machine_id": 21555,
                    "bundle_id": 1075358098,
                    "actual_status": "running",
                    "intended_status": "running",
                    "image_uuid": "kernelkind/oracle-mvp@sha256:" + "4" * 64,
                    "gpu_name": "RTX PRO 6000 WS",
                    "num_gpus": 1,
                    "disk_space": 200.0,
                    "dph_total": 1.64,
                    "is_bid": False,
                    "verification": "verified",
                    "label": "crec-72-gte-full-build",
                    "jupyter_token": "must-not-survive",
                    "extra_env": [["-e", "DOCKER_LOGIN=must-not-survive"]],
                    "ssh_host": "must-not-survive",
                    "ssh_port": 12345,
                }
            ]
        }

        records = sanitize_instance_list(raw)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["id"], 88001234)
        self.assertEqual(records[0]["label"], "crec-72-gte-full-build")
        self.assertNotIn("jupyter_token", records[0])
        self.assertNotIn("extra_env", records[0])
        self.assertNotIn("ssh_host", records[0])
        self.assertNotIn("ssh_port", records[0])

        with self.assertRaisesRegex(ValueError, "list"):
            sanitize_instance_list({"instances": {"id": 88001234}})

    def test_create_result_discards_instance_credentials(self):
        raw = {
            "success": True,
            "new_contract": 88001234,
            "instance_api_key": "must-not-survive",
        }

        record = freeze_create_result(raw)
        self.assertEqual(record, {"success": True, "new_contract": 88001234})


if __name__ == "__main__":
    unittest.main()

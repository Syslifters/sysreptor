scoutsuite_results =
{
    "account_id": "123456789012",
    "provider_name": "Amazon Web Services",
    "services": {
        "s3": {
            "findings": {
                "s3-bucket-allowing-cleartext": {
                    "level": "danger",
                    "description": "S3 bucket allows cleartext (HTTP) requests",
                    "rationale": "Data in transit should be encrypted using HTTPS.",
                    "references": ["https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html"],
                    "items": [
                        "regions.eu-west-1.buckets.bucket-one",
                        "regions.eu-west-1.buckets.bucket-two"
                    ]
                },
                "s3-bucket-versioning-disabled": {
                    "level": "warning",
                    "description": "S3 bucket versioning is disabled",
                    "rationale": "Versioning protects against accidental deletion and overwrites.",
                    "references": [],
                    "items": ["regions.eu-west-1.buckets.bucket-three"]
                }
            }
        },
        "iam": {
            "findings": {
                "iam-password-policy-expiration": {
                    "level": "good_practice",
                    "description": "Password expiration policy is configured",
                    "rationale": "",
                    "references": [],
                    "items": ["regions.global.password_policy"]
                }
            }
        }
    }
};

# coding=utf-8

from typing import Any

import requests

from ..util import format_datetime
from .alerter import Alerter, register


@register
class BulkSMSAlerter(Alerter):
    """Send SMS alerts using the BulkSMS service.

    Subscription required, see http://www.bulksms.co.uk"""

    type = "bulksms"

    def __init__(self, config_options: dict) -> None:
        super().__init__(config_options)
        self.username = self.get_config_option(
            "username", required=True, allow_empty=False
        )
        self.password = self.get_config_option(
            "password", required=True, allow_empty=False
        )
        self.target = self.get_config_option("target", required=True, allow_empty=False)

        self.sender = self.get_config_option("sender", default="SmplMntr")
        assert isinstance(self.sender, str)
        if len(self.sender) > 11:
            self.alerter_logger.warning("truncating SMS sender name to 11 chars")
            self.sender = self.sender[:11]

        self.api_host = self.get_config_option("api_host", default="www.bulksms.co.uk")

        self.support_catchup = True

    def send_alert(self, name: str, monitor: Any) -> None:
        """Send an SMS alert."""

        if not monitor.urgent:
            return

        type_ = self.should_alert(monitor)
        message = ""
        url = ""

        # to reassure mypy, else params has a bad type later
        assert isinstance(self.username, str)
        assert isinstance(self.password, str)
        assert isinstance(self.target, str)
        assert isinstance(self.sender, str)

        downtime = monitor.get_downtime()
        if type_ == "":
            return
        elif type_ == "catchup":
            message = "catchup: %s failed on %s at %s (%s)\n%s" % (
                name,
                monitor.running_on,
                format_datetime(monitor.first_failure_time()),
                downtime,
                monitor.get_result(),
            )
            if len(message) > 160:
                self.alerter_logger.warning("Truncating SMS message to 160 chars.")
                message = message[:156] + "..."
            url = "https://{}/eapi/submission/send_sms/2/2.0".format(self.api_host)
            params = {
                "username": self.username,
                "password": self.password,
                "message": message,
                "msisdn": self.target,
                "sender": self.sender,
                "repliable": "0",
            }
        elif type_ == "failure":
            message = "%s failed on %s at %s (%s)\n%s" % (
                name,
                monitor.running_on,
                format_datetime(monitor.first_failure_time()),
                downtime,
                monitor.get_result(),
            )
            if len(message) > 160:
                self.alerter_logger.warning("Truncating SMS message to 160 chars.")
                message = message[:156] + "..."
            url = "https://{}/eapi/submission/send_sms/2/2.0".format(self.api_host)
            params = {
                "username": self.username,
                "password": self.password,
                "message": message,
                "msisdn": self.target,
                "sender": self.sender,
                "repliable": "0",
            }
        else:
            # we don't handle other types of message
            pass

        if url == "":
            return

        if not self.dry_run:
            try:
                r = requests.get(url, params=params)
                s = r.text
                if not s.startswith("0"):
                    self.alerter_logger.error(
                        "Unable to send SMS: %s (%s)", s.split("|")[0], s.split("|")[1]
                    )
                    self.available = False
            except Exception:
                self.alerter_logger.exception("SMS sending failed")
                self.available = False
        else:
            self.alerter_logger.info("dry_run: would send SMS: %s", url)
        return

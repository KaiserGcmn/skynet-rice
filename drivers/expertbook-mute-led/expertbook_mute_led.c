// SPDX-License-Identifier: GPL-2.0
/*
 * Speaker mute LED companion for ASUS ExpertBook B3405CCA on Linux 6.12.
 * WMI endpoint documented by Jorge Nunez Granero's asus-wmi patch:
 * https://lists.openwall.net/linux-kernel/2026/09/18/2801
 * Use the existing ASUS WMI transport; do not replace its platform driver.
 */
#include <linux/dmi.h>
#include <linux/leds.h>
#include <linux/module.h>
#include <linux/platform_data/x86/asus-wmi.h>

#define EXPERTBOOK_SPEAKER_LED 0x0004001c

static int expertbook_led_set(struct led_classdev *led,
			     enum led_brightness brightness)
{
	return asus_wmi_evaluate_method(ASUS_WMI_METHODID_DEVS,
		EXPERTBOOK_SPEAKER_LED, brightness != LED_OFF, NULL);
}

static struct led_classdev expertbook_led = {
	.name = "platform::mute",
	.max_brightness = 1,
	.default_trigger = "audio-mute",
	.brightness_set_blocking = expertbook_led_set,
	.flags = LED_CORE_SUSPENDRESUME | LED_REJECT_NAME_CONFLICT,
};

static int __init expertbook_led_init(void)
{
	u32 status = 0;
	int ret;

	if (!dmi_match(DMI_SYS_VENDOR, "ASUSTeK COMPUTER INC.") ||
	    !dmi_match(DMI_PRODUCT_NAME, "ASUS EXPERTBOOK B3405CCA"))
		return -ENODEV;

	ret = asus_wmi_evaluate_method(ASUS_WMI_METHODID_DSTS,
		EXPERTBOOK_SPEAKER_LED, 0, &status);
	if (ret)
		return ret;
	if (status == U32_MAX || !(status & ASUS_WMI_DSTS_PRESENCE_BIT)) {
		pr_info("expertbook_mute_led: firmware does not expose speaker LED\n");
		return -ENODEV;
	}

	ret = led_classdev_register(NULL, &expertbook_led);
	if (!ret)
		pr_info("expertbook_mute_led: registered speaker LED, status %#x\n",
			status);
	return ret;
}

static void __exit expertbook_led_exit(void)
{
	led_classdev_unregister(&expertbook_led);
}

module_init(expertbook_led_init);
module_exit(expertbook_led_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("ASUS ExpertBook B3405CCA speaker mute LED companion");
MODULE_VERSION("0.1");
MODULE_SOFTDEP("pre: asus_nb_wmi snd_ctl_led");

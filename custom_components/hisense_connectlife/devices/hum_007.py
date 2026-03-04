"""Schema for Dehumidifier (007) device type."""

from .base import DeviceAttribute, DeviceSchema

HUMIDITY_007 = DeviceSchema(
    device_type="007",
    feature_code="",
    attributes={
        "t_work_mode": DeviceAttribute(
            key="t_work_mode",
            name="设定模式",
            attr_type="Enum",
            step=1,
            value_range="1, 0, 15, 5, 6, 16, 3",
            value_map={
                "0": "持续",
                "1": "正常",
                "2": "自动",
                "3": "干衣",
            },
            read_write="RW",
        ),
        "t_humidity": DeviceAttribute(
            key="t_humidity",
            name="设定湿度值",
            attr_type="Number",
            step=5,
            value_range="30~80",
            read_write="RW",
        ),
        "f_humidity": DeviceAttribute(
            key="f_humidity",
            name="实际湿度",
            attr_type="Number",
            step=1,
            value_range="30~90",
            read_write="R",
        ),
        "t_power": DeviceAttribute(
            key="t_power",
            name="开关机",
            attr_type="Enum",
            step=1,
            value_range="0,1",
            value_map={"0": "关", "1": "开"},
            read_write="RW",
        ),
        "t_fan_speed": DeviceAttribute(
            key="t_fan_speed",
            name="设定风速",
            attr_type="Enum",
            step=1,
            value_range="0,5,6,7,8,9",
            value_map={
                "2": "自动",
                "3": "中风",
                "1": "高风",
                "0": "低风",
            },
            read_write="RW",
        ),
        "f_power_consumption": DeviceAttribute(
            key="f_power_consumption",
            name="电量累积消耗值",
            attr_type="Number",
            read_write="R",
        ),
    },
)

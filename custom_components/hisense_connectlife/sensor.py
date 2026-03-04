"""Platform for Hisense AC sensor integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    StatusKey,
)
from .coordinator import HisenseACPluginDataUpdateCoordinator
from .entity_descriptions import SensorEntityConfig, fault_sensor
from .models import DeviceInfo as HisenseDeviceInfo

_LOGGER = logging.getLogger(__name__)

# Define sensor types
SENSOR_TYPES: dict[str, SensorEntityConfig] = {
    # --- Measurement sensors ---
    "indoor_temperature": SensorEntityConfig(
        key=StatusKey.TEMPERATURE,
        name="Indoor Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfTemperature.CELSIUS,
        description="Current indoor temperature",
    ),
    "power_consumption": SensorEntityConfig(
        key=StatusKey.CONSUMPTION,
        name="Power Consumption",
        icon="mdi:flash",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        description="Accumulated power consumption",
    ),
    "electricity": SensorEntityConfig(
        key=StatusKey.ENERGY,
        name="Electric Current",
        icon="mdi:current-ac",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfElectricCurrent.AMPERE,
        description="Current electric current",
    ),
    "voltage": SensorEntityConfig(
        key=StatusKey.VOLTAGE,
        name="Voltage",
        icon="mdi:sine-wave",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfElectricPotential.VOLT,
        description="Current voltage",
    ),
    "power_display": SensorEntityConfig(
        key=StatusKey.POWER_DISPLAY,
        name="Power",
        icon="mdi:flash",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfPower.WATT,
        description="Current power consumption",
    ),
    "indoor_humidity": SensorEntityConfig(
        key=StatusKey.FHUMIDITY,
        name="Indoor Humidity",
        icon="mdi:water-percent",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        unit="%",
        description="Current indoor humidity",
    ),
    "water_tank_temp": SensorEntityConfig(
        key=StatusKey.WATER_TANK_TEMP,
        name="Water Tank Temp",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfTemperature.CELSIUS,
        description="Current water tank temperature",
    ),
    "in_water_temp": SensorEntityConfig(
        key=StatusKey.IN_WATER_TEMP,
        name="In Water Temp",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfTemperature.CELSIUS,
        description="Current in water temperature",
    ),
    "out_water_temp": SensorEntityConfig(
        key=StatusKey.OUT_WATER_TEMP,
        name="Out Water Temp",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfTemperature.CELSIUS,
        description="Current out water temperature",
    ),
    "f_zone1water_temp1": SensorEntityConfig(
        key=StatusKey.ZONE1WATER_TEMP1,
        name="温区1实际值",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfTemperature.CELSIUS,
        description="Current out water temperature",
    ),
    "f_zone2water_temp2": SensorEntityConfig(
        key=StatusKey.ZONE2WATER_TEMP2,
        name="温区2实际值",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        unit=UnitOfTemperature.CELSIUS,
        description="Current out water temperature",
    ),
    # --- Fault sensors ---
    "f_e_intemp": fault_sensor(StatusKey.F_E_INTEMP, "室内温度传感器故障"),
    "f_e_incoiltemp": fault_sensor(
        StatusKey.F_E_INCOILTEMP, "室内盘管温度传感器故障"
    ),
    "f_e_inhumidity": fault_sensor(
        StatusKey.F_E_INHUMIDITY, "室内湿度传感器故障"
    ),
    "f_e_infanmotor": fault_sensor(
        StatusKey.F_E_INFANMOTOR, "室内风机电机运转异常故障"
    ),
    "f_e_arkgrille": fault_sensor(StatusKey.F_E_ARKGRILLE, "柜机格栅保护告警"),
    "f_e_invzero": fault_sensor(StatusKey.F_E_INVZERO, "室内电压过零检测故障"),
    "f_e_incom": fault_sensor(StatusKey.F_E_INCOM, "室内外通信故障"),
    "f_e_indisplay": fault_sensor(
        StatusKey.F_E_INDISPLAY, "室内控制板与显示板通信故障"
    ),
    "f_e_inkeys": fault_sensor(
        StatusKey.F_E_INKEYS, "室内控制板与按键板通信故障"
    ),
    "f_e_inwifi": fault_sensor(
        StatusKey.F_E_INWIFI, "WIFI控制板与室内控制板通信故障"
    ),
    "f_e_inele": fault_sensor(
        StatusKey.F_E_INELE, "室内控制板与室内电量板通信故障"
    ),
    "f_e_ineeprom": fault_sensor(
        StatusKey.F_E_INEEPROM, "室内控制板EEPROM出错"
    ),
    "f_e_outeeprom": fault_sensor(StatusKey.F_E_OUTEEPROM, "室外EEPROM出错"),
    "f_e_outcoiltemp": fault_sensor(
        StatusKey.F_E_OUTCOILTEMP, "室外盘管温度传感器故障"
    ),
    "f_e_outgastemp": fault_sensor(
        StatusKey.F_E_OUTGASTEMP, "排气温度传感器故障"
    ),
    "f_e_outtemp": fault_sensor(
        StatusKey.F_E_OUTTEMP, "室外环境温度传感器故障"
    ),
    "f_e_push": fault_sensor(StatusKey.F_E_PUSH, "推送故障"),
    "f_e_waterfull": fault_sensor(StatusKey.F_E_WATERFULL, "水满报警"),
    "f_e_upmachine": fault_sensor(
        StatusKey.F_E_UPMACHINE, "室内（上部）直流风机电机运转异常故障"
    ),
    "f_e_dwmachine": fault_sensor(
        StatusKey.F_E_DWMACHINE, "室外（下部）直流风机电机运转异常故障"
    ),
    "f_e_filterclean": fault_sensor(
        StatusKey.F_E_FILTERCLEAN, "过滤网清洁告警"
    ),
    "f_e_wetsensor": fault_sensor(StatusKey.F_E_WETSENSOR, "湿敏传感器故障"),
    "f_e_tubetemp": fault_sensor(StatusKey.F_E_TUBETEMP, "管温传感器故障"),
    "f_e_temp": fault_sensor(StatusKey.F_E_TEMP, "室温传感器故障"),
    "f_e_pump": fault_sensor(StatusKey.F_E_PUMP, "水泵故障"),
    "f_e_exhaust_hightemp": fault_sensor(
        StatusKey.F_E_EXHAUST_HIGHTEMP, "排气温度过高"
    ),
    "f_e_high_pressure": fault_sensor(StatusKey.F_E_HIGH_PRESSURE, "高压故障"),
    "f_e_low_pressure": fault_sensor(StatusKey.F_E_LOW_PRESSURE, "低压故障"),
    "f_e_wire_drive": fault_sensor(StatusKey.F_E_WIRE_DRIVE, "通信故障"),
    "f_e_coiltemp": fault_sensor(StatusKey.F_E_COILTEMP, "盘管温度传感器故障"),
    "f_e_env_temp": fault_sensor(StatusKey.F_E_ENV_TEMP, "环境温度传感器故障"),
    "f_e_exhaust": fault_sensor(StatusKey.F_E_EXHAUST, "排气温度传感器故障"),
    "f_e_inwater": fault_sensor(StatusKey.F_E_INWATER, "进水温度传感器故障"),
    "f_e_water_tank": fault_sensor(
        StatusKey.F_E_WATER_TANK, "水箱温度传感器故障"
    ),
    "f_e_return_air": fault_sensor(
        StatusKey.F_E_RETURN_AIR, "回气温度传感器故障"
    ),
    "f_e_outwater": fault_sensor(StatusKey.F_E_OUTWATER, "出水温度传感器故障"),
    "f_e_solar_temperature": fault_sensor(
        StatusKey.F_E_SOLAR_TEMPERATURE, "太阳能温度传感器故障"
    ),
    "f_e_compressor_overload": fault_sensor(
        StatusKey.F_E_COMPRESSOR_OVERLOAD, "压缩机过载"
    ),
    "f_e_excessive_current": fault_sensor(
        StatusKey.F_E_EXCESSIVE_CURRENT, "电流过大"
    ),
    "f_e_fan_fault": fault_sensor(StatusKey.F_E_FAN_FAULT, "风机故障"),
    "f_e_displaycom_fault": fault_sensor(
        StatusKey.F_E_DISPLAYCOM_FAULT, "显示板通信故障"
    ),
    "f_e_upwatertank_fault": fault_sensor(
        StatusKey.F_E_UPWATERTANK_FAULT, "水箱上部温度传感器故障"
    ),
    "f_e_downwatertank_fault": fault_sensor(
        StatusKey.F_E_DOWNWATERTANK_FAULT, "水箱下部温度传感器故障"
    ),
    "f_e_suctiontemp_fault": fault_sensor(
        StatusKey.F_E_SUCTIONTEMP_FAULT, "吸气温度传感器故障"
    ),
    "f_e_e2data_fault": fault_sensor(
        StatusKey.F_E_E2DATA_FAULT, "EEPROM数据故障"
    ),
    "f_e_drivecom_fault": fault_sensor(
        StatusKey.F_E_DRIVECOM_FAULT, "驱动板通信故障"
    ),
    "f_e_drive_fault": fault_sensor(StatusKey.F_E_DRIVE_FAULT, "驱动板故障"),
    "f_e_returnwatertemp_fault": fault_sensor(
        StatusKey.F_E_RETURNWATERTEMP_FAULT, "回水温度传感器故障"
    ),
    "f_e_clockchip_fault": fault_sensor(
        StatusKey.F_E_CLOCKCHIP_FAULT, "时钟芯片故障"
    ),
    "f_e_eanode_fault": fault_sensor(
        StatusKey.F_E_EANODE_FAULT, "电子阳极故障"
    ),
    "f_e_powermodule_fault": fault_sensor(
        StatusKey.F_E_POWERMODULE_FAULT, "电量模块故障"
    ),
    "f_e_fan_fault_tip": fault_sensor(
        StatusKey.F_E_FAN_FAULT_TIP, "外风机故障"
    ),
    "f_e_pressuresensor_fault_tip": fault_sensor(
        StatusKey.F_E_PRESSURESENSOR_FAULT_TIP, "压力传感器故障"
    ),
    "f_e_tempfault_solarwater_tip": fault_sensor(
        StatusKey.F_E_TEMPFAULT_SOLARWATER_TIP, "太阳能水温感温故障"
    ),
    "f_e_tempfault_mixedwater_tip": fault_sensor(
        StatusKey.F_E_TEMPFAULT_MIXEDWATER_TIP, "混水感温故障"
    ),
    "f_e_tempfault_balance_watertank_tip": fault_sensor(
        StatusKey.F_E_TEMPFAULT_BALANCE_WATERTANK_TIP, "平衡水箱感温故障"
    ),
    "f_e_tempfault_eheating_outlet_tip": fault_sensor(
        StatusKey.F_E_TEMPFAULT_EHEATING_OUTLET_TIP, "内置电加热出水感温故障"
    ),
    "f_e_tempfault_refrigerant_outlet_tip": fault_sensor(
        StatusKey.F_E_TEMPFAULT_REFRIGERANT_OUTLET_TIP, "冷媒出口温感故障"
    ),
    "f_e_tempfault_refrigerant_inlet_tip": fault_sensor(
        StatusKey.F_E_TEMPFAULT_REFRIGERANT_INLET_TIP, "冷媒进口温感故障"
    ),
    "f_e_inwaterpump_tip": fault_sensor(
        StatusKey.F_E_INWATERPUMP_TIP, "内置水泵故障"
    ),
    "f_e_outeeprom_tip": fault_sensor(
        StatusKey.F_E_OUTEEPROM_TIP, "外机EEPROM故障"
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Hisense AC sensor platform."""
    coordinator: HisenseACPluginDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    try:
        # Get devices from coordinator
        devices = coordinator.data
        _LOGGER.debug("Setting up sensors with coordinator data: %s", devices)

        if not devices:
            _LOGGER.warning("No devices found in coordinator data")
            return

        entities = []
        for device_id, device in devices.items():
            _LOGGER.debug(
                "Processing device for sensors: %s", device.to_dict()
            )
            if isinstance(device, HisenseDeviceInfo) and device.is_devices():
                # Add sensors for each supported feature
                for sensor_type, sensor_info in SENSOR_TYPES.items():
                    # Check if the device supports this attribute
                    parser = coordinator.api_client.parsers.get(
                        device.device_id
                    )
                    if device.has_attribute(sensor_info.key, parser):
                        if (
                            device.status.get("f_zone2_select") == "0"
                            and sensor_type == "f_zone2water_temp2"
                        ):
                            continue
                        _LOGGER.info(
                            "Adding  sensor for device    %s: %s",
                            device.feature_code,
                            sensor_info.name,
                        )
                        # 判断是否是故障传感器
                        is_fault_sensor = (
                            sensor_info.device_class == SensorDeviceClass.ENUM
                        )

                        # 获取当前值
                        current_value = device.status.get(sensor_info.key)
                        # 故障传感器特殊处理：值为0或None时跳过
                        if is_fault_sensor:
                            if current_value is None or current_value == "0":
                                continue
                        entity = HisenseSensor(
                            coordinator, device, sensor_type, sensor_info
                        )
                        entities.append(entity)
                    status_list = device.failed_data
                    if not status_list:
                        continue
                    # 在遍历传感器类型时：
                    if sensor_type in status_list:  # 仅检查键是否存在
                        _LOGGER.info(
                            "添加告警 %s sensor for device: %s",
                            sensor_info.name,
                            device.name,
                        )
                        entity = HisenseSensor(
                            coordinator, device, sensor_type, sensor_info
                        )
                        entities.append(entity)
            else:
                _LOGGER.warning(
                    "Skipping unsupported device: %s-%s (%s)",
                    getattr(device, "type_code", None),
                    getattr(device, "feature_code", None),
                    getattr(device, "name", None),
                )

        if not entities:
            _LOGGER.warning("No supported sensors found")
            return

        _LOGGER.info("Adding %d sensor entities", len(entities))
        async_add_entities(entities)

    except Exception as err:
        _LOGGER.error("Failed to set up sensor platform: %s", err)
        raise


class HisenseSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Hisense AC sensor."""

    coordinator: HisenseACPluginDataUpdateCoordinator
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HisenseACPluginDataUpdateCoordinator,
        device: HisenseDeviceInfo,
        sensor_type: str,
        sensor_info: SensorEntityConfig,
    ) -> None:
        super().__init__(coordinator)
        self._device_id: str = device.device_id
        self._sensor_type = sensor_type
        self._sensor_key = sensor_info.key
        self._sensor_info = sensor_info
        self._attr_unique_id = f"{device.device_id}_{sensor_type}"
        self._attr_name = sensor_info.name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            name=device.name,
            manufacturer="Hisense",
            model=f"{device.type_name} ({device.feature_name})",
        )
        self._attr_icon = sensor_info.icon
        self._attr_device_class = sensor_info.device_class
        self._attr_state_class = sensor_info.state_class
        self._attr_native_unit_of_measurement = sensor_info.unit
        self._attr_entity_registry_enabled_default = True

    def _handle_coordinator_update(self) -> None:
        device = self.coordinator.get_device(self._device_id)
        if not device:
            _LOGGER.warning(
                "Device %s not found during sensor update", self._device_id
            )
            return
        """处理协调器更新，实现动态实体管理"""
        # 获取当前设备状态 (reuse the already-fetched device)
        current_value = device.get_status_value(self._sensor_key)

        # 故障传感器特殊处理
        if self._sensor_info.device_class == SensorDeviceClass.ENUM:
            # 当值变为0或无效时移除实体
            if current_value in (None, "0"):
                _LOGGER.info(
                    "Removing fault sensor %s (current value: %s)",
                    self.entity_id,
                    current_value,
                )
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        "entity_registry",
                        "remove",
                        {"entity_id": self.entity_id},
                    )
                )
                return  # 终止后续处理

        # 调用父类处理更新
        super()._handle_coordinator_update()

    @property
    def name(self) -> str:
        """动态获取翻译后的名称"""
        hass = self.hass
        translation_key = self._sensor_type  # 使用传感器类型作为键
        current_lang = hass.config.language
        translations = hass.data.get(f"{DOMAIN}.translations", {}).get(
            current_lang, {}
        )
        translated_name = translations.get(
            translation_key, self._sensor_info.name
        )
        return translated_name

    @property
    def _device(self):
        """Get current device data from coordinator."""
        return self.coordinator.get_device(self._device_id)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not super().available:  # 继承父类的可用性检查（设备在线）
            return False
        current_mode = self._device.get_status_value(
            StatusKey.MODE
        )  # 使用正确键名
        # 判断自动模式
        if current_mode in ["3"]:
            _LOGGER.debug("设备处于自动模式，温度控制不可用")
            return False
        if self._sensor_type == "f_zone2water_temp2":
            allowed_modes = {"0", "6"}  # 仅允许制热和制热+制热水模式
            if current_mode not in allowed_modes:
                return False

        return True

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""
        if not self._device:
            return None
        value = self._device.get_status_value(self._sensor_key)
        if value is None:
            return None

        try:
            if self._attr_device_class == SensorDeviceClass.ENUM:
                return value
            numeric = float(value)
            # f_electricity is reported in mA, convert to A
            if self._sensor_key == StatusKey.ENERGY:
                numeric /= 1000.0
            # f_humidity: API returns 128 (0x80) as "not available"
            if self._sensor_key == StatusKey.FHUMIDITY and numeric == 128:
                return None
            return numeric
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Could not convert %s value '%s' to float",
                self._attr_name,
                value,
            )
            return None

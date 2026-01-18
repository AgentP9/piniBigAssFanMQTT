# OpenHAB Configuration Guide for BigAssFan MQTT Integration

## Issue Resolution

The fan wasn't reacting to OpenHAB commands because of a value range mismatch. OpenHAB dimmers typically send percentage values (0-100), but the BigAssFan MQTT bridge expects raw values:
- **Fan speed**: 0-7 (not 0-100)
- **Light level**: 0-16 (not 0-100)

## MQTT Behavior

### Light Power and Level Relationship
When controlling the light via power switch:
- **ON**: Sets light level to 2 and publishes both `light_power=ON` and `light_level=2`
- **OFF**: Sets light level to 0 and publishes both `light_power=OFF` and `light_level=0`

### MQTT Flow
When commands are received on `/set` topics, the bridge:
1. Executes the command on the fan
2. Reads back the current state from the fan
3. Publishes the new state to the status topic(s)

**Example:**
```
Publish: haiku_fan/light_power/set = ON
→ Bridge sets light to level 2
→ Bridge publishes: haiku_fan/light_power = ON
→ Bridge publishes: haiku_fan/light_level = 2
```

## Solution

Configure OpenHAB to send raw values instead of percentages. You have two options:

### Option 1: Use Number Items Instead of Dimmers (Recommended)

Replace the dimmer items with number items that use the correct ranges:

**things:**
```
Type switch : mqtt_bigassfan_power     "BigAssFan Power"       [ stateTopic="haiku_fan/power", commandTopic="haiku_fan/power/set" ]
Type number : mqtt_bigassfan_speed     "BigAssFan Speed"       [ stateTopic="haiku_fan/speed", commandTopic="haiku_fan/speed/set", min=0, max=7 ]
Type switch : mqtt_bigassfan_lightpwr  "BigAssFan Light Power" [ stateTopic="haiku_fan/light_power", commandTopic="haiku_fan/light_power/set" ]
Type number : mqtt_bigassfan_light     "BigAssFan Light Level" [ stateTopic="haiku_fan/light_level", commandTopic="haiku_fan/light_level/set", min=0, max=16 ]
```

**items:**
```
Switch BigAssFan_Power       "BigAssFan Power"       { channel="mqtt:topic:oha21b14:mqtt_bigassfan_power" }
Number BigAssFan_Speed       "BigAssFan Speed [%d]"  { channel="mqtt:topic:oha21b14:mqtt_bigassfan_speed" }
Switch BigAssFan_LightPower  "BigAssFan Light Power" { channel="mqtt:topic:oha21b14:mqtt_bigassfan_lightpwr" }
Number BigAssFan_Light       "BigAssFan Light [%d]"  { channel="mqtt:topic:oha21b14:mqtt_bigassfan_light" }
```

### Option 2: Use Transformations with Dimmers

If you want to keep using dimmers in the UI, use transformation maps to convert between percentages and raw values:

**Create transformation files:**

`transform/speed_to_raw.map`:
```
0=0
14=1
28=2
43=3
57=4
71=5
86=6
100=7
```

`transform/speed_to_percent.map`:
```
0=0
1=14
2=28
3=43
4=57
5=71
6=86
7=100
```

`transform/light_to_raw.map`:
```
0=0
6=1
12=2
19=3
25=4
31=5
38=6
44=7
50=8
56=9
62=10
69=11
75=12
81=13
88=14
94=15
100=16
```

`transform/light_to_percent.map`:
```
0=0
1=6
2=12
3=19
4=25
5=31
6=38
7=44
8=50
9=56
10=62
11=69
12=75
13=81
14=88
15=94
16=100
```

**things:**
```
Type switch : mqtt_bigassfan_power     "BigAssFan Power"       [ stateTopic="haiku_fan/power", commandTopic="haiku_fan/power/set" ]
Type dimmer : mqtt_bigassfan_speed     "BigAssFan Speed"       [ stateTopic="haiku_fan/speed", commandTopic="haiku_fan/speed/set", transformationPattern="MAP:speed_to_percent.map", transformationPatternOut="MAP:speed_to_raw.map" ]
Type switch : mqtt_bigassfan_lightpwr  "BigAssFan Light Power" [ stateTopic="haiku_fan/light_power", commandTopic="haiku_fan/light_power/set" ]
Type dimmer : mqtt_bigassfan_light     "BigAssFan Light Level" [ stateTopic="haiku_fan/light_level", commandTopic="haiku_fan/light_level/set", transformationPattern="MAP:light_to_percent.map", transformationPatternOut="MAP:light_to_raw.map" ]
```

## Testing

After updating your configuration, test the integration:

1. **Test fan power:**
   ```
   mosquitto_pub -h <mqtt-broker> -t "haiku_fan/power/set" -m "ON"
   ```

2. **Test fan speed (raw value 0-7):**
   ```
   mosquitto_pub -h <mqtt-broker> -t "haiku_fan/speed/set" -m "3"
   ```

3. **Test light level (raw value 0-16):**
   ```
   mosquitto_pub -h <mqtt-broker> -t "haiku_fan/light_level/set" -m "8"
   ```

## MQTT Topics Reference

### Status Topics (Published by the service)
- `haiku_fan/name` - Fan name
- `haiku_fan/power` - Fan power state (ON/OFF)
- `haiku_fan/speed` - Fan speed (0-7)
- `haiku_fan/light_power` - Light power state (ON/OFF)
- `haiku_fan/light_level` - Light brightness level (0-16)
- `haiku_fan/state` - All states as JSON

### Command Topics (Subscribed by the service)
- `haiku_fan/power/set` - Set fan power (payload: `ON` or `OFF`)
- `haiku_fan/speed/set` - Set fan speed (payload: `0` to `7`)
- `haiku_fan/light_power/set` - Set light power (payload: `ON` or `OFF`)
- `haiku_fan/light_level/set` - Set light brightness (payload: `0` to `16`)

# Capability Report: LG HDR WQHD

Total controls: 57

| Code | Name | Access | Type | Max | Safe Class |
|------|------|--------|------|-----|------------|
| 2 | New Control Value | Read+Write | enum | 2 | safe_write_restore |
| 4 | Restore Factory Defaults | Write Only | writeonly | 255 | safe_write_restore |
| 5 | Restore Factory Luminance/Contrast | Write Only | writeonly | 1 | safe_write_restore |
| 6 | Restore Factory Geometry Defaults | Write Only | writeonly | 255 | safe_write_restore |
| 8 | Restore Factory Color Defaults | Write Only | writeonly | 255 | safe_write_restore |
| 0B | Color Temperature Increment | Read Only | readonly | - | safe_read |
| 0C | Color Temperature Request | Read+Write | range | 100 | safe_write_restore |
| 0E | Clock | Read+Write | range | 100 | safe_write_restore |
| 10 | Brightness | Read+Write | range | 100 | safe_write_restore |
| 12 | Contrast | Read+Write | range | 100 | safe_write_restore |
| 14 | Select Color Preset | Read+Write | range | 11 | safe_write_restore |
| 15 | LG Picture Mode Select | Read+Write | enum | 255 | safe_write_restore |
| 16 | Video Gain (Drive): Red | Read+Write | range | 100 | safe_write_restore |
| 18 | Video Gain (Drive): Green | Read+Write | range | 100 | safe_write_restore |
| 1A | Video Gain (Drive): Blue | Read+Write | range | 100 | safe_write_restore |
| 1E | Auto Setup | Read+Write | range | 2 | safe_write_restore |
| 20 | Horizontal Position (Phase) | Read+Write | range | 100 | safe_write_restore |
| 30 | Vertical Position (Phase) | Read+Write | range | 100 | safe_write_restore |
| 3E | Clock Phase | Read+Write | range | 100 | safe_write_restore |
| 45 | LG Gamma Selection | Read+Write | enum | 255 | safe_write_restore |
| 4D | LG Six-Axis Color: Red Hue | Read+Write | range | 65535 | experimental |
| 4E | LG Six-Axis Color: Green Hue | Read+Write | range | 65535 | experimental |
| 4F | LG Six-Axis Color: Blue Hue | Read+Write | range | 65535 | experimental |
| 52 | Active Control | Read Only | readonly | - | safe_read |
| 60 | Input Select | Read+Write | enum | 18 | safe_write_restore |
| 62 | Audio: Speaker Volume | Read+Write | range | 100 | safe_write_restore |
| 6C | Video Black Level: Red | Read+Write | range | 100 | experimental |
| 6E | Video Black Level: Green | Read+Write | range | 100 | experimental |
| 70 | Video Black Level: Blue | Read+Write | range | 100 | experimental |
| 87 | Sharpness | Read+Write | range | 100 | safe_write_restore |
| 8D | Audio Mute / Screen Blank | Read+Write | enum | 100 | safe_write_restore |
| AC | Horizontal Frequency | Read Only | readonly | - | safe_read |
| B6 | Display Technology Type | Read Only | readonly | - | safe_read |
| C0 | Display Usage Time | Read Only | readonly | - | safe_read |
| C6 | Application Enable Key | Read Only | readonly | - | safe_read |
| C8 | Display Controller ID | Read+Write | range | 255 | manual_only |
| C9 | Display Firmware Level | Read Only | readonly | - | safe_read |
| CA | OSD | Read+Write | enum | 2 | manual_only |
| CC | OSD Language | Read+Write | enum | 16 | manual_only |
| D6 | Power Mode | Read+Write | enum | 5 | safe_write_restore |
| DF | VCP Version | Read Only | readonly | - | safe_read |
| E4 | LG Black Stabilizer | Read+Write | range | 255 | experimental |
| E7 | LG Six-Axis Color: Cyan Hue | Read+Write | range | 65535 | experimental |
| E8 | LG Six-Axis Color: Magenta Hue | Read+Write | range | 255 | experimental |
| E9 | LG Six-Axis Color: Yellow Hue | Read+Write | range | 255 | experimental |
| EA | LG Six-Axis Color: Red Saturation | Read+Write | range | 255 | experimental |
| EB | LG DFC (Digital Fine Contrast) | Read+Write | enum | 1 | safe_write_restore |
| EF | LG Six-Axis Color: Green Saturation | Read+Write | range | 65535 | experimental |
| F4 | LG Display Port Version Select | Read+Write | range | 65535 | manual_only |
| F5 | LG Aspect Ratio Policy | Read+Write | enum | 255 | safe_write_restore |
| F6 | LG Smart Energy Saving | Read+Write | enum | 255 | safe_write_restore |
| F7 | LG Response Time (Overdrive) | Read+Write | enum | 255 | safe_write_restore |
| F8 | LG Local Dimming Mode | Read+Write | enum | 255 | experimental |
| F9 | LG Crosshair Feature | Read+Write | range | 255 | experimental |
| FA | LG Factory Settings Menu Lock | Read+Write | range | 255 | blocked |
| FB | LG Audio Source Route | Read+Write | enum | 65535 | manual_only |
| FE | LG Power LED Indicator | Read+Write | enum | 255 | safe_write_restore |
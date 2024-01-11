> [!NOTE]
> This is hard fork of  [JaccoR](https://github.com/JaccoR/hass-entso-e)'s very nice but apparently abandoned project. I'll make an effort to maintain it and any possible bugs. Much functionality has been removed so pls make an 'issue' if you need really need it. And I'll put it on HACS, if they let me, but until then just put the files in `custom_components`. 

# Home Assistant ENTSO-e Transparency Platform Energy Prices
Custom component for Home Assistant to fetch energy prices of all European countries from the ENTSO-e Transparency Platform (https://transparency.entsoe.eu/).
Day ahead energy prices are added as a sensor and can be used in automations to switch equipment. A 24 Hour forecast of the energy prices is in the sensors attributes and can be shown in a graph:


<img src="https://github.com/andreas-berg/hass-entsoe-dayahead/assets/39428693/2fb7e32c-b93a-4277-9dbd-0135eece885a" height="300"> | <img height="300" src="https://github.com/andreas-berg/hass-entsoe-dayahead/assets/39428693/cfeca581-b129-46d1-abee-d6d3418d6a4d">
:-------------------------:|:-------------------------:
"Middle Finger" - pricing  |  Kinect Energy sent a "wrong bid" = Black Friday consumption party
Bidding Zone: FI @ 18.9.2023 | Bidding Zone: FI @ 24.11.2023


### API Access
You need an ENTSO-e Restful API key for this integration. To request this API key, register on the [Transparency Platform](https://transparency.entsoe.eu/) and send an email to transparency@entsoe.eu with “Restful API access” in the subject line. Indicate the
email address you entered during registration in the email body.

### Sensors
The integration adds the following sensors:
- ~~Average Day-Ahead Electricity Price Today (This integration carries attributes with all prices)~~
- ~~Highest Day-Ahead Electricity Price Today~~
- ~~Lowest Day-Ahead Electricity Price Today~~
- ~~Current Day-Ahead Electricity Price~~
- ~~Current Percentage Relative To Highest Electricity Price Of The Day~~
- ~~Next Hour Day-Ahead Electricity Price~~
- ~~Time Of Highest Energy Price Today~~
- ~~Time Of Lowest Energy Price Today~~
- Todays Prices
- Tomorrows Prices
------
## Installation

### Manual
Download this repository and place the contents of `custom_components` in your own `custom_components` map of your Home Assistant installation. Restart Home Assistant and add the integration through your settings. 

### HACS (not available yet)

~~Search for "ENTSO-e" when adding HACS integrations and add "ENTSO-e Transparency Platform". Restart Home Assistant and add the integration through your settings.~~

------
## Configuration

The sensors can be added using the web UI. In the web UI you can add your API-key and country and the sensors will automatically be added to your system. 

### ApexChart Graph
Prices can be shown using the [ApexChart Graph Card](https://github.com/RomRider/apexcharts-card) like in the example above. The Lovelace code for this graph is given below:
(Should work to just add an ApexCharts-Card and replace all yaml in the editor window with this)
```
type: custom:apexcharts-card
apex_config:
  chart:
    width: 100%
  grid:
    borderColor: rgba(255,255,255,0.1)
  xaxis:
    tooltip:
      enabled: false
  yaxis:
    tickAmount: 5
    tooltip:
      formatter: |
        EVAL:function(val, opts) {
          return val + "c/kWh";
        }
experimental:
  color_threshold: true
graph_span: 1d
header:
  title: Elpris imorgon (cnt/kWh)
  show: true
span:
  start: day
  offset: +1d
series:
  - entity: sensor.entsoe_prices_tomorrow
    name: Spot
    type: line
    curve: stepline
    stroke_width: 2
    color_threshold:
      - value: -100
        color: blue
        opacity: 1
      - value: 0
        color: rgb(115, 191, 105)
        opacity: 1
      - value: 10
        color: rgb(250, 222, 42)
      - value: 20
        color: rgb(255, 152, 48)
      - value: 40
        color: rgb(242, 73, 92)
      - value: 60
        color: rgb(163, 82, 204)
    data_generator: |
      return entity.attributes.prices_tomorrow.map((item, index) => {
        return [new Date(item["time"]).getTime(), entity.attributes.prices_tomorrow[index]["price"]];
      });
```





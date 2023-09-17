> [!NOTE]
> This is hard fork of  [JaccoR](https://github.com/JaccoR/hass-entso-e)'s very nice but apparently abandoned project. I'll make an effort to maintain it and any possible bugs. Much functionality has been removed so pls make an 'issue' if you need really need it. And I'll put it on HACS, if they let me, but until then just put the files in `custom_components`. 

# Home Assistant ENTSO-e Transparency Platform Energy Prices
Custom component for Home Assistant to fetch energy prices of all European countries from the ENTSO-e Transparency Platform (https://transparency.entsoe.eu/).
Day ahead energy prices are added as a sensor and can be used in automations to switch equipment. A 24 Hour forecast of the energy prices is in the sensors attributes and can be shown in a graph:

<p align="center">
    <img src="https://user-images.githubusercontent.com/31140879/195382579-c87b3285-c599-4e30-867e-1acf9feffabe.png" width=40% height=40%>
</p>

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

```
type: custom:apexcharts-card
graph_span: 24h
span:
  start: day
now:
  show: true
  label: Now
header:
  show: true
  title: Electriciteitsprijzen Vandaag (€/kwh)
yaxis:
  - decimals: 2
series:
  # This is the entity ID with no name configured.
  # When a name is configured it will be sensor.<name>_average_electricity_price_today.
  - entity: sensor.average_electricity_price_today
    stroke_width: 2
    float_precision: 3
    type: column
    opacity: 1
    color: ''
    data_generator: |
      return entity.attributes.prices.map((entry) => { 
      return [new Date(entry.time), entry.price];
      });

```





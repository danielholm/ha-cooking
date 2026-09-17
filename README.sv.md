# Matlagning

En helper-integration för Home Assistant som lägger måltemperatur, förvarning
och hålltid ovanpå **vilka temperatursensorer som helst**.

Den äger ingen hårdvara. Du pekar ut en kärntemperatursensor och eventuellt en
omgivningssensor, och får larmen och tidtagningen som saknas. Fungerar lika bra
på en BLE-probe, en ugnsgivare, en Zigbee-termometer i jäskorgen eller en
Shelly med temperaturingång.

Skapa en instans per sak du lagar. Har du två probes blir det två instanser.

## Installation

Lägg till repot som custom repository i HACS, eller kopiera
`custom_components/cooking/` till din `config/custom_components/`. Starta om.

Sedan **Inställningar → Enheter och tjänster → Lägg till integration →
Matlagning**.

Varje instans blir en egen enhet, med alla sina entiteter samlade på ett
enhetskort.

## Entiteter

| Entitet | Typ | Beskrivning |
|---|---|---|
| Förinställning | select | Rekommenderade temperaturer, se nedan |
| Måltemperatur | number | Mål för kärnan |
| Förvarning | number | Grader innan målet |
| Hålltemp min | number | Undre gräns för hållspannet |
| Hålltemp max | number | Övre gräns, 0 = inget tak |
| Hålltid | number | Minuter, 0 = av |
| Snart klar | binary_sensor | Latchad förvarning |
| Måltemp uppnådd | binary_sensor | Latchat larm |
| Inom hållspann | binary_sensor | Ögonblicksvärde |
| Hålltid klar | binary_sensor | Latchat larm |
| Hålltid uppnådd | sensor | Ackumulerade sekunder |
| Stigningstakt | sensor | °C/h |
| Beräknad tid kvar | sensor | Grov gissning |
| Återställ | button | Nollställer larm och klocka |

## Hålltid

Tiden är **ackumulerad, inte sammanhängande**. Öppnar du ugnsluckan pausas
klockan och fortsätter sedan där den var. För pastörisering är ackumulerat det
enda korrekta, och för bakning är det nästan alltid det man vill ha.

Två mekanismer skyddar mot skräp:

**Hysteres på två grader.** Temperaturen vaggar alltid något, och utan marginal
skulle klockan starta och stanna hela tiden kring tröskeln. Marginalen är
asymmetrisk — det är tuffare att komma in i spannet än att falla ur.

**Luckor över fem minuter räknas inte.** Har sensorn varit borta är den tiden
inte verifierad hålltid, och antas därför inte.

Hålltiden överlever omstart. En fyra timmar lång jäsning nollställs inte av en
HA-uppdatering.

## Beräknad tid kvar

Linjär extrapolation över de senaste tio minuterna. Den är förvånansvärt
användbar under uppvärmningsfasen och **fel under stall** — den fas där
avdunstningen håller en brisket stilla på 68 grader i timmar. Sensorn blir
`unknown` när stigningstakten är för låg för en seriös gissning, istället för
att ljuga.

Det här är i grunden vad Meater tar betalt för. Behandla den som en
fingervisning, inte ett löfte.

## Förinställningar

Kärntemperaturerna följer Livsmedelsverkets rekommendationer där sådana finns
(fågel, malet kött, fläsk), och etablerad praxis där det handlar om önskad
tillagningsgrad snarare än säkerhet (nöt, lamm). Kontrollera själv vid känslig
tillagning — listan är en bekvämlighet, inte en auktoritet.

Några sätter hållspann istället för måltemp:

- **Surdeg – jäsning**: 24–26 °C i fyra timmar
- **Surdegsgrund – matning**: 22–25 °C i sex timmar
- **Ugn – 200 °C i 20 min**: mäts på omgivningssensorn
- **Rökning – 110 °C**: 105–120 °C, ingen tidsgräns

Ändrar du en siffra för hand hoppar väljaren till `Anpassad`. Att välja en
förinställning nollställer larmen, eftersom det gamla larmet inte längre gäller.

## Automation

```yaml
alias: Matlagning - klart
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.black_maltemp_uppnadd
      - binary_sensor.white_maltemp_uppnadd
      - binary_sensor.surdeg_halltid_klar
    to: "on"
actions:
  - action: script.meddela_daniel
    data:
      meddelande: "{{ trigger.to_state.name }}"
mode: queued
max: 3
```

## Tester

```
python3 tests/test_calc.py
```

Beräkningslogiken i `calc.py` importerar ingenting från Home Assistant och kan
köras fristående.

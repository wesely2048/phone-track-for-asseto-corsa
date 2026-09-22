**Two descriptions are available below: English and Russian. / Ниже представлены два описания: на английском и русском языках.**

[English](#english) · [Русский](#русский)

---

<a id="english"></a>

# ZIG SIM → OpenTrack Bridge

A small, free bridge between an iPhone's motion sensors and OpenTrack. The script receives the phone's orientation from **ZIG SIM** over the local network, converts the quaternion into **Yaw / Pitch / Roll** angles, and forwards them to OpenTrack. This makes it possible to use an iPhone as a physical in-game camera controller in Assetto Corsa and other games that support FreeTrack or TrackIR.

The project uses only Python's standard library. No additional `pip` packages are required.

## Features

- control the in-game camera by physically rotating an iPhone;
- three rotational axes: Yaw, Pitch, and Roll;
- automatic calibration on startup;
- recentering without restarting the bridge;
- portrait and landscape phone orientations;
- independent direction control for every axis;
- local-network communication;
- no third-party Python dependencies.

## Limitations

The bridge provides **3DOF rotational tracking**. It does not track physical movement forward, backward, upward, downward, or sideways. For in-car footage, this provides camera panning, tilting, and natural handheld roll, but it is not full 6DOF positional tracking.

## How it works

```text
iPhone running ZIG SIM
        │ UDP / JSON / Quaternion
        ▼
zigsim_opentrack_bridge.py
        │ UDP / 6 × Float64
        ▼
OpenTrack
        │ FreeTrack / TrackIR
        ▼
Assetto Corsa
```

## Requirements

- an iPhone with a gyroscope;
- Windows 10 or Windows 11;
- [ZIG SIM from the App Store](https://apps.apple.com/app/zig-sim/id1112909974);
- [Python 3](https://www.python.org/downloads/windows/) or Python from the Microsoft Store;
- [OpenTrack](https://github.com/opentrack/opentrack/releases);
- the iPhone and PC connected to the same local network.

## Project files

```text
README.md
zigsim_opentrack_bridge.py
```

## Installation

### 1. Install Python

Download Python only from [python.org](https://www.python.org/downloads/windows/) or the Microsoft Store. When using the python.org installer, enable:

```text
Add Python to PATH
```

Verify the installation in Command Prompt:

```cmd
py --version
```

### 2. Install OpenTrack

Download the latest installer from the [official OpenTrack releases page](https://github.com/opentrack/opentrack/releases) and install it.

### 3. Install ZIG SIM

Install [ZIG SIM](https://apps.apple.com/app/zig-sim/id1112909974) from the App Store on the iPhone.

### 4. Download the project

Clone or download this repository. Keep `README.md` and `zigsim_opentrack_bridge.py` in the same folder.

## Network configuration

The phone and PC must be connected to the same local network. The PC may use Ethernet while the iPhone uses Wi-Fi, provided both devices can communicate inside the network.

### Finding the PC's IP address

Open Windows Command Prompt and run:

```cmd
ipconfig
```

Find the `IPv4 Address` of the active network adapter, for example:

```text
192.168.1.105
```

Do not use `127.0.0.1` or an address belonging to VMware, VirtualBox, or a VPN adapter.

## ZIG SIM configuration

Create a ZIG SIM connection with these settings:

| Setting | Value |
|---|---|
| Protocol | UDP |
| Message format | JSON |
| Destination IP | The PC's IPv4 address |
| Destination port | `50000` |
| Rate | 60 FPS |

Enable this sensor:

```text
QUATERNION
```

The other sensors can be disabled. The bridge expects JSON packets; OSC packets are not supported directly.

When prompted for the first time, allow ZIG SIM to access the local network:

```text
iPhone Settings → Privacy & Security → Local Network
```

## OpenTrack configuration

Configure OpenTrack as follows:

| Setting | Value |
|---|---|
| Input | `UDP over network` |
| Input port | `4242` |
| Output | `freetrack 2.0 Enhanced` |
| Filter | `Accela` |

Open the `freetrack 2.0 Enhanced` settings and select:

```text
Both
```

Under `Options → Shortcuts`, the following bindings are recommended:

```text
Center: F10
Toggle tracking: F9
```

## Running the bridge

Open the project folder in Windows File Explorer. Click the address bar, type `cmd`, and press Enter.

For a phone held horizontally, run:

```cmd
py zigsim_opentrack_bridge.py --orientation landscape-left
```

If the phone is held in the opposite landscape orientation:

```cmd
py zigsim_opentrack_bridge.py --orientation landscape-right
```

For portrait orientation:

```cmd
py zigsim_opentrack_bridge.py --orientation portrait
```

A successful launch displays:

```text
Listening for ZIG SIM JSON on UDP 0.0.0.0:50000
Sending OpenTrack packets to 127.0.0.1:4242
```

### Recommended startup order

1. Start OpenTrack and click **Start**.
2. Start `zigsim_opentrack_bridge.py`.
3. Hold the iPhone in the position that should be treated as neutral.
4. Start data transmission in ZIG SIM.
5. Wait for the `Centered` message in the bridge console.
6. Confirm that OpenTrack's pink octopus follows the phone's rotations.
7. Launch Assetto Corsa.

## Bridge controls

| Action | Control |
|---|---|
| Recenter | Press Enter |
| Stop normally | Type `q` and press Enter |
| Force stop | Press `Ctrl+C` |

Keep the phone still in its neutral position while recentering.

## Debug mode

Add `--debug` to display the calculated angles:

```cmd
py zigsim_opentrack_bridge.py --orientation landscape-left --debug
```

The console will display values such as:

```text
Yaw   15.20  Pitch   -4.10  Roll    2.30
```

## Correcting reversed axes

If an axis moves in the wrong direction, change its sign:

```cmd
py zigsim_opentrack_bridge.py --orientation landscape-left --yaw-sign 1
```

Available sign options:

```text
--yaw-sign -1 or 1
--pitch-sign -1 or 1
--roll-sign -1 or 1
```

Example with inverted roll:

```cmd
py zigsim_opentrack_bridge.py --orientation landscape-left --roll-sign -1
```

Axes can also be inverted under `OpenTrack → Options → Output`.

## Command-line options

Display the built-in help:

```cmd
py zigsim_opentrack_bridge.py --help
```

| Option | Purpose | Default |
|---|---|---|
| `--listen-port` | Port receiving ZIG SIM data | `50000` |
| `--opentrack-port` | OpenTrack input port | `4242` |
| `--orientation` | Phone orientation | `landscape-left` |
| `--yaw-sign` | Yaw direction | `-1` |
| `--pitch-sign` | Pitch direction | `-1` |
| `--roll-sign` | Roll direction | `1` |
| `--debug` | Print calculated angles | disabled |

Supported phone orientations:

```text
portrait
portrait-upside-down
landscape-left
landscape-right
```

## OpenTrack mapping for a handheld-camera effect

For natural handheld footage, use nearly linear mapping curves:

| iPhone rotation | In-game camera rotation |
|---:|---:|
| 0° | 0° |
| 10° | 10° |
| 30° | 30° |
| 60° | 60° |
| 90° | 90° |

Do not disable Roll: a small amount of horizon tilt makes the footage feel handheld. Heavy filtering increases latency, so begin with the default Accela settings.

## Using it in Assetto Corsa

The easiest way to record footage is from a saved replay:

1. Record a drive or open an existing replay.
2. Select an in-car camera.
3. Position the camera in the driver's or passenger's seat.
4. Start OpenTrack, the bridge, and ZIG SIM transmission.
5. Recenter the phone.
6. Control the camera direction by moving the iPhone.
7. Record the result with OBS Studio or another screen-capture application.

## Troubleshooting

### The bridge runs but never displays `Centered`

Check that:

- ZIG SIM uses `JSON`, not `OSC`;
- the `QUATERNION` sensor is enabled;
- ZIG SIM contains the correct PC IPv4 address;
- the ZIG SIM destination port is `50000`;
- the phone and PC are on the same network;
- ZIG SIM has permission to access the local network.

### `Packets arrive, but no quaternion was found`

The packets reach the PC, but they do not contain orientation data. Enable `QUATERNION` in ZIG SIM and verify that the message format is `JSON`.

### Windows blocks the connection

On the first launch, allow Python to communicate on **private networks**. If Windows does not display a prompt, create an inbound Windows Firewall rule:

```text
Protocol: UDP
Local port: 50000
Action: Allow
Profile: Private
```

Router port forwarding is not required.

### OpenTrack's octopus does not move

Check that:

- OpenTrack input is set to `UDP over network`;
- the input port is `4242`;
- OpenTrack tracking has been started;
- another OpenTrack instance is not already using the port;
- the bridge console displays `Centered`.

### Camera movement is jerky

- connect the iPhone to a 5 GHz Wi-Fi network;
- set ZIG SIM to 60 FPS;
- disable VPN connections on the phone and PC;
- try the Accela filter;
- avoid excessive smoothing.

### The camera starts from the wrong position

Hold the phone in the required neutral position and press Enter in the bridge console. The next valid packet becomes the new center position.

## Security and privacy

- The bridge receives UDP packets only on local port `50000`.
- Tracking data is forwarded to OpenTrack through `127.0.0.1`, so this part of the connection never leaves the PC.
- The script does not access the internet, save received tracking data, or require administrator privileges.
- On a home network, allow Python only under the **Private network** firewall profile.

## Technical details

ZIG SIM sends the iPhone's orientation quaternion in a JSON packet. The bridge:

1. locates the quaternion inside the packet;
2. normalizes it;
3. stores the initial orientation during calibration;
4. calculates rotation relative to the calibrated position;
5. converts that rotation into Yaw, Pitch, and Roll;
6. creates six `Float64` values in the order `X, Y, Z, Yaw, Pitch, Roll`;
7. sends the packet to OpenTrack at `127.0.0.1:4242`.

The positional values `X`, `Y`, and `Z` are always sent as zero.



---

<a id="русский"></a>

# ZIG SIM → OpenTrack Bridge — описание на русском языке

Небольшой бесплатный мост между гироскопом iPhone и OpenTrack. Скрипт принимает ориентацию телефона из **ZIG SIM** по локальной сети, преобразует quaternion в углы **Yaw / Pitch / Roll** и передаёт их в OpenTrack. Это позволяет использовать iPhone как физический контроллер камеры в Assetto Corsa и других играх с поддержкой FreeTrack/TrackIR.

Проект использует только стандартную библиотеку Python — устанавливать дополнительные пакеты через `pip` не требуется.

## Возможности

- управление направлением игровой камеры поворотами iPhone;
- три вращательные оси: Yaw, Pitch и Roll;
- автоматическая калибровка при запуске;
- повторная центровка без перезапуска;
- поддержка вертикального и горизонтального положения телефона;
- настройка направления каждой оси;
- передача данных по локальной сети;
- отсутствие внешних Python-зависимостей.

## Ограничения

Скрипт обеспечивает вращательное отслеживание **3DOF**. Он не передаёт физическое перемещение телефона вперёд, назад, вверх, вниз или в стороны. Для съёмки из салона автомобиля это даёт поворот, наклон и естественный завал виртуальной камеры, но не полноценное позиционное отслеживание 6DOF.

## Схема работы

```text
iPhone с ZIG SIM
        │ UDP / JSON / Quaternion
        ▼
zigsim_opentrack_bridge.py
        │ UDP / 6 × Float64
        ▼
OpenTrack
        │ FreeTrack / TrackIR
        ▼
Assetto Corsa
```

## Требования

- iPhone с гироскопом;
- Windows 10 или Windows 11;
- [ZIG SIM из App Store](https://apps.apple.com/app/zig-sim/id1112909974);
- [Python 3](https://www.python.org/downloads/windows/) или Python из Microsoft Store;
- [OpenTrack](https://github.com/opentrack/opentrack/releases);
- iPhone и компьютер в одной локальной сети.

## Файлы проекта

```text
README.md
zigsim_opentrack_bridge.py
```

## Установка

### 1. Установите Python

Скачайте Python только с [python.org](https://www.python.org/downloads/windows/) или из Microsoft Store. Во время установки версии с python.org включите параметр:

```text
Add Python to PATH
```

Проверьте установку в командной строке:

```cmd
py --version
```

### 2. Установите OpenTrack

Скачайте актуальный установщик со страницы [официальных релизов OpenTrack](https://github.com/opentrack/opentrack/releases) и установите программу.

### 3. Установите ZIG SIM

Установите [ZIG SIM](https://apps.apple.com/app/zig-sim/id1112909974) из App Store на iPhone.

### 4. Скачайте проект

Скачайте репозиторий через GitHub или поместите файлы `README.md` и `zigsim_opentrack_bridge.py` в одну папку.

## Настройка сети

Телефон и компьютер должны быть подключены к одной локальной сети. Компьютер может быть подключён к роутеру кабелем, а iPhone — по Wi-Fi: важно, чтобы устройства видели друг друга внутри сети.

### Как узнать IP-адрес компьютера

Откройте командную строку Windows и выполните:

```cmd
ipconfig
```

Найдите `IPv4 Address` активного подключения, например:

```text
192.168.1.105
```

Не используйте адреса виртуальных адаптеров VMware, VirtualBox, VPN или `127.0.0.1`.

## Настройка ZIG SIM

Создайте в ZIG SIM соединение со следующими параметрами:

| Параметр | Значение |
|---|---|
| Protocol | UDP |
| Message format | JSON |
| Destination IP | IPv4-адрес компьютера |
| Destination port | `50000` |
| Rate | 60 FPS |

В списке датчиков включите:

```text
QUATERNION
```

Остальные датчики можно отключить. Скрипт принимает именно JSON; пакеты OSC напрямую не поддерживаются.

При первом запуске разрешите ZIG SIM доступ к локальной сети:

```text
Настройки iPhone → Конфиденциальность и безопасность → Локальная сеть
```

## Настройка OpenTrack

В главном окне OpenTrack установите:

| Параметр | Значение |
|---|---|
| Input | `UDP over network` |
| Input port | `4242` |
| Output | `freetrack 2.0 Enhanced` |
| Filter | `Accela` |

Откройте настройки `freetrack 2.0 Enhanced` и выберите режим:

```text
Both
```

В `Options → Shortcuts` рекомендуется назначить:

```text
Center: F10
Toggle tracking: F9
```

## Запуск

Откройте папку проекта в проводнике Windows. Нажмите на адресную строку, введите `cmd` и нажмите Enter.

Для телефона в горизонтальном положении выполните:

```cmd
py zigsim_opentrack_bridge.py --orientation landscape-left
```

Если телефон повёрнут горизонтально в другую сторону:

```cmd
py zigsim_opentrack_bridge.py --orientation landscape-right
```

Для вертикального положения:

```cmd
py zigsim_opentrack_bridge.py --orientation portrait
```

При успешном запуске появятся сообщения:

```text
Listening for ZIG SIM JSON on UDP 0.0.0.0:50000
Sending OpenTrack packets to 127.0.0.1:4242
```

### Рекомендуемый порядок запуска

1. Запустите OpenTrack и нажмите **Start**.
2. Запустите `zigsim_opentrack_bridge.py`.
3. Возьмите iPhone в положение, которое должно считаться центральным.
4. Запустите передачу данных в ZIG SIM.
5. Дождитесь сообщения `Centered` в окне скрипта.
6. Убедитесь, что розовый осьминог OpenTrack повторяет движения телефона.
7. Запустите Assetto Corsa.

## Управление скриптом

| Действие | Команда |
|---|---|
| Повторная центровка | нажать Enter |
| Завершение работы | ввести `q` и нажать Enter |
| Принудительное завершение | `Ctrl+C` |

Во время центровки держите телефон неподвижно в нейтральном положении.

## Диагностический режим

Чтобы видеть вычисленные углы, добавьте `--debug`:

```cmd
py zigsim_opentrack_bridge.py --orientation landscape-left --debug
```

В консоли будут отображаться значения:

```text
Yaw   15.20  Pitch   -4.10  Roll    2.30
```

## Настройка направлений

Если какая-либо ось движется в противоположную сторону, измените её знак:

```cmd
py zigsim_opentrack_bridge.py --orientation landscape-left --yaw-sign 1
```

Доступные параметры:

```text
--yaw-sign -1 или 1
--pitch-sign -1 или 1
--roll-sign -1 или 1
```

Пример с инвертированным креном:

```cmd
py zigsim_opentrack_bridge.py --orientation landscape-left --roll-sign -1
```

Ось также можно инвертировать в `OpenTrack → Options → Output`.

## Все параметры командной строки

```cmd
py zigsim_opentrack_bridge.py --help
```

| Параметр | Назначение | Значение по умолчанию |
|---|---|---|
| `--listen-port` | Порт получения данных ZIG SIM | `50000` |
| `--opentrack-port` | Входной порт OpenTrack | `4242` |
| `--orientation` | Положение телефона | `landscape-left` |
| `--yaw-sign` | Направление Yaw | `-1` |
| `--pitch-sign` | Направление Pitch | `-1` |
| `--roll-sign` | Направление Roll | `1` |
| `--debug` | Вывод текущих углов | выключен |

Допустимые положения телефона:

```text
portrait
portrait-upside-down
landscape-left
landscape-right
```

## Настройка OpenTrack для эффекта ручной камеры

Для естественного эффекта съёмки с телефона рекомендуется использовать почти линейные кривые:

| Поворот iPhone | Поворот камеры |
|---:|---:|
| 0° | 0° |
| 10° | 10° |
| 30° | 30° |
| 60° | 60° |
| 90° | 90° |

Не отключайте Roll: небольшой завал горизонта создаёт ощущение настоящей ручной съёмки. Сильное сглаживание увеличивает задержку, поэтому сначала рекомендуется попробовать стандартные параметры фильтра Accela.

## Использование в Assetto Corsa

Для съёмки футажа удобнее работать с повтором заезда:

1. Запишите заезд или откройте готовый повтор.
2. Выберите камеру из салона автомобиля.
3. Установите точку камеры на водительском или пассажирском месте.
4. Запустите OpenTrack, мост и передачу ZIG SIM.
5. Выполните центровку.
6. Управляйте направлением камеры движениями iPhone.
7. Записывайте результат через OBS Studio или другое приложение захвата экрана.

## Устранение неполадок

### Скрипт работает, но не появляется сообщение `Centered`

Проверьте:

- в ZIG SIM выбран формат `JSON`, а не `OSC`;
- включён датчик `QUATERNION`;
- в ZIG SIM указан правильный IPv4 компьютера;
- порт назначения ZIG SIM равен `50000`;
- телефон и компьютер находятся в одной сети;
- ZIG SIM разрешён доступ к локальной сети.

### Появляется сообщение `Packets arrive, but no quaternion was found`

Пакеты доходят до компьютера, но не содержат ориентацию. Включите `QUATERNION` в ZIG SIM и убедитесь, что выбран формат `JSON`.

### Windows блокирует соединение

При первом запуске разрешите Python доступ к **частным сетям**. Если запрос не появился, создайте входящее правило брандмауэра Windows:

```text
Тип: UDP
Локальный порт: 50000
Действие: разрешить
Профиль: частный
```

Открывать порт на роутере и настраивать переадресацию портов не требуется.

### Осьминог OpenTrack не двигается

Проверьте:

- выбран ли в OpenTrack вход `UDP over network`;
- установлен ли порт `4242`;
- нажат ли **Start**;
- не занят ли порт другим экземпляром OpenTrack;
- появляется ли в консоли скрипта сообщение `Centered`.

### Камера движется рывками

- подключите iPhone к сети Wi-Fi 5 ГГц;
- установите в ZIG SIM частоту 60 FPS;
- закройте VPN на телефоне и компьютере;
- попробуйте фильтр Accela;
- не устанавливайте чрезмерно сильное сглаживание.

### Камера начинает движение из неправильного положения

Удерживайте телефон в требуемом центральном положении и нажмите Enter в окне скрипта. Следующий корректный пакет будет принят как новое нулевое положение.

## Безопасность и конфиденциальность

- Скрипт принимает UDP-пакеты только на локальном порту `50000`.
- Данные отправляются из скрипта в OpenTrack через адрес `127.0.0.1` и не покидают компьютер.
- Скрипт не обращается к интернету, не сохраняет полученные данные и не требует прав администратора.
- Для домашней сети рекомендуется разрешать Python только в профиле **Частная сеть**.

## Как это работает

ZIG SIM отправляет quaternion ориентации iPhone в JSON-пакете. Скрипт:

1. находит quaternion в пакете;
2. нормализует его;
3. запоминает исходную ориентацию при центровке;
4. вычисляет поворот относительно исходного положения;
5. переводит результат в Yaw, Pitch и Roll;
6. формирует пакет из шести чисел `Float64` в порядке `X, Y, Z, Yaw, Pitch, Roll`;
7. отправляет пакет в OpenTrack на `127.0.0.1:4242`.

Позиционные значения `X`, `Y` и `Z` передаются равными нулю.

## Проверка проекта


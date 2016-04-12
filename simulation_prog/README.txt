hexstack


Dieses kleine Programm simuliert das "frozen bottle" setup in einem Grafik-Fenster.

Daten werden über ein UDP port empfangen. Default port ist 12345.

Datenformat ist 3 bytes pro Zelle, R,G,B, ohne header. Ein UDP paket ist ein update.

Benötigt SDL2.

Bauen in Windows VisualStudio mit 'sln' und 'vcxproj' Projekt-Datei für VisualStudio 12,

Bauen in Linux mit gcc mit der Kommandozeile in 'compile'.


Zum Ausprobieren liegt das kleine Python Programm "try_LED_send_UDP.py" bei, welches bunte Sequenzen an den port sendet.


## Deployment auf den Server kopieren (WinSCP)

Um die Anwendung auf den Server zu übertragen, können Sie WinSCP verwenden:

1. **WinSCP herunterladen und installieren:**  
    [https://winscp.net/](https://winscp.net/)

2. **Mit dem Server verbinden:**  
    - Starten Sie WinSCP.
    - Geben Sie Hostname, Benutzername und Passwort ein.
    - Wählen Sie das Protokoll (meist SFTP oder FTP).

3. **Dateien kopieren:**  
    - Navigieren Sie im linken Fenster zu Ihrem lokalen Deployment-Ordner.
    - Navigieren Sie im rechten Fenster zum Zielverzeichnis auf dem Server.
    - Ziehen Sie die gewünschten Dateien von links nach rechts.

4. **Verbindung trennen:**  
    Nach erfolgreichem Kopieren können Sie die Verbindung schließen.

**Hinweis:**  
Stellen Sie sicher, dass Sie die richtigen Zugriffsrechte für das Zielverzeichnis besitzen.

docker installieren

### Docker unter Ubuntu/Debian installieren

1. **System aktualisieren:**
    ```bash
    sudo apt update && sudo apt upgrade
    ```

2. **Notwendige Pakete installieren:**
    ```bash
    sudo apt install ca-certificates curl gnupg
    ```

3. **Docker-Repository hinzufügen:**
    ```bash
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    ```

4. **Docker installieren:**
    ```bash
    sudo apt update
    sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    ```

5. **Docker-Dienst starten und aktivieren:**
    ```bash
    sudo systemctl start docker
    sudo systemctl enable docker
    ```

6. **Installation testen:**
    ```bash
    sudo docker run hello-world
    ```

**Hinweis:** Für andere Distributionen (z. B. CentOS, Fedora) sind die Befehle ähnlich, aber die Paketverwaltung ist anders (yum, dnf).


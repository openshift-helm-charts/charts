### To deploy Helm chart of Streebo Chatbot, Clone this directory
1. Clone this repository
2. Install Helm on the System
3. Open terminal and browse to "streebo-chatbot" folder
4. Add the redhat service account registry secret to values.yaml.for properties in imagePullSecretsConfig registrySecret & connectRegistry
5. Browse back to cloned folder (>>> cd ..)
6. To install helm on the system, Execute the following command
    >>> helm install <helm name> streebo-chatbot
    Sample command: 
    >>> helm install chatbot Streebo-chatbot

7. To list helm
    >>> helm list

8. To uninstall the helm
    >>> helm delete <helm name>
    Sample command:
    >>> helm delete chatbot

## Что такое Kaniko?

Чтобы работать с Kaniko и автоматизировать процесс сборки Docker-образов, используя Kaniko с Docker Compose или без него, нужно выполнить несколько шагов.


`Kaniko` — это инструмент для сборки Docker-образов в Kubernetes или других контейнеризованных средах. Kaniko работает в контейнере и не требует наличия Docker Daemon на машине, что делает его полезным для работы в CI/CD процессах или в контейнерных средах.

##  Как начать работу с Kaniko

Установка Kaniko

Если вы хотите использовать Kaniko локально (на своей машине), вам нужно сначала установить Docker и Docker Compose.
- Установите Docker:
- Установите Docker Compose:

После этого можно начать использовать Kaniko. Для локальной работы вы можете запускать его в контейнере, используя команду Docker.

Использование Docker Compose с Kaniko: Если вы используете Docker Compose, чтобы собрать несколько сервисов, Kaniko может работать с файлами docker-compose.yml.

#### Требования:
- У вас должен быть Dockerfile.
- Вам нужно аутентифицироваться в реестре (например, Docker Hub или Google Container Registry). 
- Убедитесь, что у вас есть права для пуша в указанный репозиторий.


#### Рекомендации

- Убедитесь, что у вас есть правильно настроенный файл Dockerfile и что все зависимости внутри вашего проекта указаны верно. 
- Для работы с приватными реестрами (например, Docker Hub или GCR) вы должны выполнить аутентификацию с помощью Docker:

```bash
docker login
```
Это обеспечит Kaniko доступ к вашему реестру.

- В случае с Google Container Registry вам нужно настроить аутентификацию с помощью файла сервисного аккаунта или командой gcloud auth configure-docker.


#### Полный пример работы с Kaniko

- Создайте проект с Dockerfile и docker-compose.yml. 
- Убедитесь, что у вас есть доступ к реестру (например, Docker Hub или Google Container Registry). 
- Запустите сборку с помощью Kaniko с правильными путями и параметрами.

```bash 
  poetry run kaniko build \
  --compose-file /home/./.wrapper_builder_1/docker-compose.yml \
  --kaniko-image gcr.io/kaniko-project/executor:latest \
  --push --destination gcr.io/my-project/my-image:tagname
```

#### Основные моменты:
- `--compose-file` указывает путь к Docker Compose или к папке с Dockerfile. 
- `--kaniko-image` указывает образ Kaniko, который будет использоваться для сборки. 
- `--push`означает, что после сборки образы будут загружены в реестр. 
- `--destination` указывает, куда отправить собранные образы (например, Docker Hub или Google Container Registry).
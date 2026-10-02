# Build stage
FROM php:8.4-cli AS build
WORKDIR /app

RUN apt-get update && apt-get install -y unzip git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
COPY --from=mlocati/php-extension-installer /usr/bin/install-php-extensions /usr/bin/install-php-extensions
RUN install-php-extensions sqlite3 opcache

COPY composer.json composer.lock* ./
RUN composer install --no-dev --optimize-autoloader --no-scripts
COPY . .

# Runtime stage
FROM php:8.4-cli
WORKDIR /app

COPY --from=mlocati/php-extension-installer /usr/bin/install-php-extensions /usr/bin/install-php-extensions
RUN install-php-extensions sqlite3 opcache

COPY --from=build /app .

ENV HOST=0.0.0.0
ENV PORT=7145
EXPOSE 7145
CMD ["php", "vendor/bin/tina4php", "serve", "--host", "0.0.0.0", "--port", "7145", "--production"]
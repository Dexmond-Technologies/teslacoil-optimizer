# ⚡ Tesla Coil Optimizer - Spring Boot Gateway Dockerfile
# Stage 1: Build the artifact
FROM maven:3.9-eclipse-temurin-17-alpine AS builder

WORKDIR /build

COPY pom.xml .
# Cache maven dependencies
RUN mvn dependency:go-offline -B

COPY src ./src
RUN mvn package -DskipTests -B

# Stage 2: Runtime image
FROM eclipse-temurin:17-jre-alpine

WORKDIR /workspace

COPY --from=builder /build/target/*.jar ./app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]

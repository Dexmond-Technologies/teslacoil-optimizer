package com.example.demo.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*") // For development, allow any origin
public class OptimizationController {

    private final RestTemplate restTemplate;
    private final String pythonServiceUrl = "http://localhost:8000/api/optimize";

    public OptimizationController() {
        this.restTemplate = new RestTemplate();
    }

    @PostMapping("/optimize")
    public ResponseEntity<Map> optimize(@RequestBody Map<String, Object> inputData) {
        // Forward the request to the Python FastAPI microservice
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(pythonServiceUrl, inputData, Map.class);
            return ResponseEntity.ok(response.getBody());
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of("error", "Python service unavailable: " + e.getMessage()));
        }
    }
}

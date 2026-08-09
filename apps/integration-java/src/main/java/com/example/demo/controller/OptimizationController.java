package com.example.demo.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class OptimizationController {

    private final RestTemplate restTemplate;

    @Value("${PYTHON_ENGINE_URL:http://localhost:8000}")
    private String pythonEngineUrl;

    public OptimizationController() {
        this.restTemplate = new RestTemplate();
    }

    @PostMapping("/optimize")
    public ResponseEntity<Map> optimize(@RequestBody Map<String, Object> inputData) {
        try {
            String targetUrl = pythonEngineUrl.endsWith("/api/optimize") 
                ? pythonEngineUrl 
                : pythonEngineUrl + "/api/optimize";
            ResponseEntity<Map> response = restTemplate.postForEntity(targetUrl, inputData, Map.class);
            return ResponseEntity.ok(response.getBody());
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of("error", "Python physics service unavailable: " + e.getMessage()));
        }
    }
}

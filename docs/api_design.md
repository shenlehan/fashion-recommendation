# API Design Document

## Overview
This document outlines the API design for the Fashion Recommendation project. It includes details about the endpoints, request and response formats, and authentication methods.

## Base URL
The base URL for the API is: `http://localhost:8000/api`

## Endpoints

### User Management

#### 1. User Registration
- **Endpoint:** `/users/register`
- **Method:** POST
- **Request Body:**
  ```json
  {
    "username": "string",
    "password": "string",
    "email": "string"
  }
  ```
- **Response:**
  - **201 Created**
    ```json
    {
      "message": "User registered successfully."
    }
    ```
  - **400 Bad Request**
    ```json
    {
      "error": "User already exists."
    }
    ```

#### 2. User Login
- **Endpoint:** `/users/login`
- **Method:** POST
- **Request Body:**
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Response:**
  - **200 OK**
    ```json
    {
      "token": "string"
    }
    ```
  - **401 Unauthorized**
    ```json
    {
      "error": "Invalid credentials."
    }
    ```

### Clothing Management

#### 3. Upload Clothing
- **Endpoint:** `/clothes/upload`
- **Method:** POST
- **Headers:** 
  - `Authorization: Bearer <token>`
- **Request Body:** (Form Data)
  - `file`: (image file)
  - `type`: "string" (e.g., "shirt", "pants", etc.)
- **Response:**
  - **201 Created**
    ```json
    {
      "message": "Clothing item uploaded successfully."
    }
    ```

#### 4. Get User Wardrobe
- **Endpoint:** `/clothes/wardrobe`
- **Method:** GET
- **Headers:** 
  - `Authorization: Bearer <token>`
- **Response:**
  - **200 OK**
    ```json
    {
      "wardrobe": [
        {
          "id": "string",
          "type": "string",
          "image_url": "string"
        }
      ]
    }
    ```

### Recommendation

#### 5. Get Recommendations
- **Endpoint:** `/recommendation`
- **Method:** POST
- **Headers:** 
  - `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "weather": {
      "temperature": "number",
      "condition": "string"
    },
    "body_type": "string"
  }
  ```
- **Response:**
  - **200 OK**
    ```json
    {
      "recommendations": [
        {
          "type": "string",
          "image_url": "string"
        }
      ],
      "missing_items": [
        "string"
      ]
    }
    ```

## Authentication
All endpoints except for user registration and login require authentication via a Bearer token. The token is obtained upon successful login and should be included in the Authorization header for subsequent requests.

## Error Handling
All responses should include appropriate HTTP status codes and error messages in the response body for error scenarios.
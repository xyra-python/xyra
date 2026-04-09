package main

import (
	"github.com/gin-gonic/gin"
	"net/http"
)

func main() {
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())

	r.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "Hello, World!",
		})
	})

	r.GET("/text", func(c *gin.Context) {
		c.String(http.StatusOK, "Hello, World!")
	})

	r.GET("/html", func(c *gin.Context) {
		c.Data(http.StatusOK, "text/html; charset=utf-8", []byte("<h1>Hello, World!</h1>"))
	})

	r.Run(":8005")
}

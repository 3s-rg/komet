package main

import (
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"
)

var data map[string]int

func loadData() {
	data = make(map[string]int)
	file, err := os.Open("shortmedia.csv")
	if err != nil {
		log.Fatalf("failed to open csv file: %v", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	_, err = reader.Read() // skip header
	if err != nil {
		log.Fatalf("failed to read csv header: %v", err)
	}

	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Fatalf("failed to read csv record: %v", err)
		}

		key := record[0] + record[1]
		size, err := strconv.Atoi(record[2])
		if err != nil {
			log.Fatalf("failed to convert size to int: %v", err)
		}
		data[key] = size
	}
}

var content []byte

func createBinaryFile() {
	content = make([]byte, 10*1024*1024) // 10 MB

	// file, err := os.Create("data.b")
	// if err != nil {
	// 	log.Fatalf("failed to create binary file: %v", err)
	// }
	// defer file.Close()

	// content := make([]byte, 10*1024*1024) // 10 MB
	for i := range content {
		content[i] = 'X'
	}

	// _, err = file.Write(content)
	// if err != nil {
	// 	log.Fatalf("failed to write to binary file: %v", err)
	// }
}

func handler(w http.ResponseWriter, r *http.Request) {
	// path := r.URL.Path[1:] // remove leading slash
	start := time.Now()

	path := r.URL.Path

	if _, exists := data[path]; !exists {
		http.NotFound(w, r)
		log.Printf("Not found: %s\n", path)
		return
	}

	log.Printf("(%d) Serving %s with %d bytes to %s\n", time.Now().UnixMilli(), path, data[path], r.RemoteAddr)

	// time.Sleep(2 * time.Second)

	w.Header().Set("Content-Type", "text/plain")

	// file, err := os.Open("data.b")
	// if err != nil {
	// 	http.Error(w, "Failed to open binary file", http.StatusInternalServerError)
	// 	return
	// }
	// defer file.Close()

	// buffer := make([]byte, data[path])
	// _, err = file.Read(buffer)
	// if err != nil {
	// 	http.Error(w, "Failed to read binary file", http.StatusInternalServerError)
	// 	return
	// }

	_, err := w.Write(content[:data[path]])
	if err != nil {
		http.Error(w, "Failed to write response", http.StatusInternalServerError)
		return
	}

	duration := time.Since(start)
	log.Printf("(%d) Served %s in %v seconds\n", time.Now().UnixMilli(), path, duration.Seconds())
}

func main() {
	loadData()
	createBinaryFile()

	http.HandleFunc("/", handler)
	port := 8000
	log.Printf("Serving at port %d\n", port)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", port), nil))
}

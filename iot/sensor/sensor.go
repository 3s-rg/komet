package main

import (
	"fmt"
	"io"
	"log"
	"math/rand"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

const (
	delay   = 2 * time.Second
	timeout = 1 * time.Second
)

var (
	name string
	HOST string
	lock sync.Mutex
)

func init() {
	log.SetFlags(log.LstdFlags | log.Lshortfile | log.Lmicroseconds)
}

func makeReq(value float64) (float64, float64, string) {
	for {
		lock.Lock()
		if HOST != "" {
			lock.Unlock()
			break
		}
		lock.Unlock()
		log.Println("Waiting for connection")
		time.Sleep(1 * time.Second)
	}

	lock.Lock()
	defer lock.Unlock()

	t1 := time.Now()

	req, err := http.NewRequest("POST", fmt.Sprintf("http://%s", HOST), strings.NewReader(fmt.Sprintf("{\"name\": \"%s\", \"value\": %f}", name, value)))

	if err != nil {
		log.Printf("Error creating request: %v", err)
		return 0, 0, HOST
	}

	client := &http.Client{Timeout: timeout}
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Error making request: %v", err)
		return 0, 0, HOST
	}

	defer resp.Body.Close()

	t2 := time.Now()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Error response: %v", resp.Status)
		return 0, 0, HOST
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Error reading response: %v", err)
		return 0, 0, HOST
	}

	response, err := strconv.ParseFloat(string(body), 64)

	if err != nil {
		log.Printf("Error parsing response: %v", err)
		return 0, 0, HOST
	}

	return t2.Sub(t1).Seconds(), response, HOST
}

func updateServerPosition(orchestratorHost, clientName string) {
	conn, _, err := websocket.DefaultDialer.Dial(fmt.Sprintf("ws://%s", orchestratorHost), nil)

	if err != nil {
		log.Fatalf("Error connecting to orchestrator: %v", err)
	}
	defer conn.Close()

	log.Printf("Connected to orchestrator at %s", orchestratorHost)

	err = conn.WriteMessage(websocket.TextMessage, []byte(clientName))
	if err != nil {
		log.Fatalf("Error sending client name: %v", err)
	}

	log.Printf("Sent client name %s", clientName)

	for {
		t, message, err := conn.ReadMessage()

		if err != nil {
			log.Printf("Error receiving server position: %v", err)
			continue
		}

		if t != websocket.TextMessage {
			log.Printf("Received non-text message: %v (type %v)", message, t)
			continue
		}

		serverPosition := string(message)
		log.Printf("Received server position %s", serverPosition)

		if serverPosition == HOST {
			continue
		}

		lock.Lock()
		HOST = serverPosition
		log.Printf("Updated HOST to %s", HOST)
		lock.Unlock()
	}
}

func main() {
	if len(os.Args) < 3 {
		fmt.Printf("Usage: %s name orchestrator_host\n", os.Args[0])
		os.Exit(1)
	}

	name = os.Args[1]
	orchestratorHost := os.Args[2]

	// seed with name
	stringToInt64 := func(s string) int64 {
		var result int64 = 0
		for _, ch := range s {
			result = result*256 + int64(ch)
		}
		return result
	}

	rng := rand.New(rand.NewSource(stringToInt64(name)))

	go updateServerPosition(orchestratorHost, name)

	time.Sleep(time.Duration(rng.Float64()) * 2 * time.Second)

	for {
		t1 := time.Now()
		val := rng.Float64() * 36.0
		ts, result, host := makeReq(val)
		log.Printf("request_info: %f,%f,%s", ts, result, host)
		t2 := time.Now()

		if t2.Sub(t1) < delay {
			time.Sleep(delay - t2.Sub(t1))
		}
	}
}

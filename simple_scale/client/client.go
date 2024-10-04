package main

import (
	"errors"
	"fmt"
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
	delay   = 1_000 * time.Millisecond
	timeout = 500 * time.Millisecond
)

var (
	name string
	HOST string
	lock sync.Mutex
)

func init() {
	log.SetFlags(log.LstdFlags | log.Lshortfile | log.Lmicroseconds)
}

func get(key string) (float64, string, error) {
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

	req, err := http.NewRequest("POST", fmt.Sprintf("http://%s/get", HOST), strings.NewReader(key))

	if err != nil {
		log.Printf("Error creating request: %v", err)
		return 0, HOST, err
	}

	client := &http.Client{Timeout: timeout}

	t1 := time.Now()
	resp, err := client.Do(req)
	delay := time.Since(t1)

	if err != nil {
		log.Printf("Error making request: %v", err)
		return 0, HOST, err
	}

	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Error response: %v", resp.Status)
		return 0, HOST, errors.New(resp.Status)
	}

	return float64(delay.Nanoseconds()) / 1e6, HOST, nil
}

func put(count int) error {
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

	req, err := http.NewRequest("POST", fmt.Sprintf("http://%s/put", HOST), strings.NewReader(fmt.Sprintf("{\"count\": %d}", count)))

	if err != nil {
		log.Printf("Error creating request: %v", err)
		return err
	}

	client := &http.Client{Timeout: 1 * time.Minute}

	t1 := time.Now()
	resp, err := client.Do(req)
	delay := time.Since(t1)

	if err != nil {
		log.Printf("Error making request: %v", err)
		return err
	}

	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		log.Printf("Error response: %v", resp.Status)
		return errors.New(resp.Status)
	}

	log.Printf("request_info: put,%f,%s", float64(delay.Nanoseconds())/1e6, HOST)

	return nil
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
		log.Printf("switch_event: %s", serverPosition)

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
	if len(os.Args) < 4 {
		fmt.Printf("Usage: %s name orchestrator_host count\n", os.Args[0])
		os.Exit(1)
	}

	name = os.Args[1]
	orchestratorHost := os.Args[2]
	count, err := strconv.Atoi(os.Args[3])

	if err != nil {
		fmt.Printf("Error parsing count: %v\n", err)
		os.Exit(1)
	}

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

	knownItems := make([]string, 0)

	put(count)

	for i := 0; i < count; i++ {
		knownItems = append(knownItems, strconv.Itoa(i))
	}

	for {
		t1 := time.Now()
		// get a random item
		key := knownItems[rng.Intn(len(knownItems))]

		tg, host, err := get(key)

		if err != nil {
			log.Printf("Error getting item: %v", err)
			log.Printf("request_info: get,0.0,%s", host)
			time.Sleep(delay)
			continue
		}

		log.Printf("request_info: get,%f,%s", tg, host)

		t2 := time.Now()
		if t2.Sub(t1) < delay {
			time.Sleep(delay - t2.Sub(t1))
		}
	}
}

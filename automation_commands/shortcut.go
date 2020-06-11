package main

import (
	"log"
	"time"
	"github.com/galaktor/gostwriter"
	"github.com/galaktor/gostwriter/key"
)

func main() {
	kb, err := gostwriter.New("foo");
	guard(err);
	ctrl, err := kb.Get(key.CODE_LEFTCTRL);  guard(err);
	alt, err := kb.Get(key.CODE_LEFTALT);  guard(err);
	c, err    := kb.Get(key.CODE_C);         guard(err);
	<-time.After(time.Millisecond*100)
	press(ctrl)
	<-time.After(time.Millisecond*100)
	press(alt)
	<-time.After(time.Millisecond*100)
	press(c)
	<-time.After(time.Millisecond*100)
	release(c)
	<-time.After(time.Millisecond*100)
	release(alt)
	<-time.After(time.Millisecond*100)
	release(ctrl)
	kb.Destroy()
}

// presses and subsequently releases a key
func push(k *gostwriter.K) {
	err := k.Push(); guard(err);
}

// presses a key, if not already pressed. does not release
func press(k *gostwriter.K) {
	err := k.Press(); guard(err);
}

// releases a key, if not aready released.
func release(k *gostwriter.K) {
	err := k.Release(); guard(err);
}

// contains boilerplate error check. if error is present,
// prints it then exits the app
func guard(e error) {
	if e != nil {
		log.Fatal(e)
	}
}
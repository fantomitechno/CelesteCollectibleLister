package main

import (
	"context"
	"fmt"
)

type App struct {
	ctx context.Context
}

func CreateCollectibleListerApp() *App {
	return &App{}
}

func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
}

func (a *App) Download(url string) string {
	return fmt.Sprintf("Downloading %s...", url)
}

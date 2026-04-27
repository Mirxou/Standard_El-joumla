/**
 * Système de logging pour le frontend
 * Utilise console en développement, peut être étendu pour envoyer les logs au serveur en production
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

class Logger {
  private isDevelopment = process.env.NODE_ENV === 'development'

  private log(level: LogLevel, message: string, ...args: any[]) {
    if (!this.isDevelopment && level === 'debug') {
      return // Ne pas logger les debug en production
    }

    const prefix = this.getPrefix(level)
    const logMessage = `${prefix} ${message}`

    switch (level) {
      case 'debug':
        console.debug(logMessage, ...args)
        break
      case 'info':
        console.info(logMessage, ...args)
        break
      case 'warn':
        console.warn(logMessage, ...args)
        break
      case 'error':
        console.error(logMessage, ...args)
        break
    }
  }

  private getPrefix(level: LogLevel): string {
    const prefixes = {
      debug: '🔍',
      info: 'ℹ️',
      warn: '⚠️',
      error: '❌'
    }
    return prefixes[level]
  }

  debug(message: string, ...args: any[]) {
    this.log('debug', message, ...args)
  }

  info(message: string, ...args: any[]) {
    this.log('info', message, ...args)
  }

  warn(message: string, ...args: any[]) {
    this.log('warn', message, ...args)
  }

  error(message: string, ...args: any[]) {
    this.log('error', message, ...args)
  }
}

export const logger = new Logger()

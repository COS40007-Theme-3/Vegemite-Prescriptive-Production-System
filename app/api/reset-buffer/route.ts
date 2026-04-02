import { NextResponse } from 'next/server'
import path from 'path'
import fs from 'fs'

export async function POST() {
  try {
    const bufferFile = path.join(process.cwd(), 'data', 'sensor_buffer.json')
    if (fs.existsSync(bufferFile)) {
      fs.unlinkSync(bufferFile)
    }
    return NextResponse.json({ status: 'success', message: 'Buffer cleared for Changeover.' })
  } catch (err) {
    return NextResponse.json({ status: 'error', message: String(err) }, { status: 500 })
  }
}
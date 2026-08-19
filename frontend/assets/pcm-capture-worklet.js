class PCM16CaptureProcessor extends AudioWorkletProcessor {
  constructor(options){
    super();
    this.targetRate=Number(options.processorOptions?.targetSampleRate||16000);
    this.ratio=sampleRate/this.targetRate;
    this.phase=0;
  }
  process(inputs){
    const input=inputs[0]?.[0];if(!input?.length)return true;
    const samples=[];let position=this.phase,sum=0;
    for(const value of input)sum+=value*value;
    while(position<input.length){
      const left=Math.floor(position),right=Math.min(input.length-1,left+1),mix=position-left;
      const value=input[left]*(1-mix)+input[right]*mix;
      samples.push(Math.max(-1,Math.min(1,value)));position+=this.ratio;
    }
    this.phase=position-input.length;
    if(samples.length){
      const pcm=new Int16Array(samples.length);
      for(let i=0;i<samples.length;i++)pcm[i]=samples[i]<0?samples[i]*0x8000:samples[i]*0x7fff;
      this.port.postMessage({type:'audio',buffer:pcm.buffer,rms:Math.sqrt(sum/input.length)},[pcm.buffer]);
    }
    return true;
  }
}
registerProcessor('oncotwin-pcm16-capture',PCM16CaptureProcessor);

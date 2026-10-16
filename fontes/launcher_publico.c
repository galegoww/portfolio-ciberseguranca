#define UNICODE
#define _UNICODE
#include <windows.h>
#include <bcrypt.h>
#include <wchar.h>
#include <stdio.h>
#include <string.h>

#define BUF 65536
static const unsigned char expected[32]={0x18,0x7f,0xec,0x8d,0xaa,0x3e,0x53,0xb6,0xbc,0x51,0xfd,0x99,0xe8,0x3d,0x0f,0xc0,0xd9,0x5c,0x2c,0x3d,0xbd,0x95,0x5a,0x74,0xd8,0x08,0xe4,0x10,0xeb,0xbb,0xf2,0x8f};
static const wchar_t *TITLE=L"DNS AI Shield Ultra";
static int fail(const wchar_t *msg){MessageBoxW(NULL,msg,TITLE,MB_OK|MB_ICONERROR);return 1;}
static int join_path(wchar_t *out,size_t count,const wchar_t *base,const wchar_t *name){return swprintf(out,count,L"%ls\\%ls",base,name)>0 && wcslen(out)<count-1;}
static int hash_file(const wchar_t *path){
 HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
 if(file==INVALID_HANDLE_VALUE)return 0;
 BCRYPT_ALG_HANDLE alg=NULL;BCRYPT_HASH_HANDLE hash=NULL;unsigned char digest[32],buffer[BUF];DWORD got=0;int ok=0;
 if(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,NULL,0)<0)goto done;
 if(BCryptCreateHash(alg,&hash,NULL,0,NULL,0,0)<0)goto done;
 while(1){if(!ReadFile(file,buffer,BUF,&got,NULL))goto done;if(!got)break;if(BCryptHashData(hash,buffer,got,0)<0)goto done;}
 if(BCryptFinishHash(hash,digest,32,0)<0)goto done;
 ok=memcmp(expected,digest,32)==0;
 done:if(hash)BCryptDestroyHash(hash);if(alg)BCryptCloseAlgorithmProvider(alg,0);CloseHandle(file);return ok;
}
int WINAPI wWinMain(HINSTANCE inst,HINSTANCE prev,PWSTR args,int show){
 (void)inst;(void)prev;(void)args;(void)show;
 wchar_t source[32768],parts[32768],part[32768],local[32768],data[32768],bin[32768],target[32768],temp[32768],name[128],command[32768];
 DWORD count=GetModuleFileNameW(NULL,source,32768);if(!count||count>=32768)return fail(L"Nao foi possivel localizar a pasta do programa.");
 wchar_t *slash=wcsrchr(source,L'\\');if(!slash)return fail(L"Caminho do programa invalido.");*slash=0;
 if(!join_path(parts,32768,source,L"dados_programa"))return fail(L"Caminho muito longo.");
 count=GetEnvironmentVariableW(L"LOCALAPPDATA",local,32768);if(!count||count>=32768)return fail(L"Nao foi possivel acessar os dados locais do Windows.");
 if(!join_path(data,32768,local,L"DNS AI Shield Ultra")||!join_path(bin,32768,data,L"bin")||!join_path(target,32768,bin,L"Shield_187fec8daa3e.exe"))return fail(L"Caminho muito longo.");
 if(!CreateDirectoryW(data,NULL)&&GetLastError()!=ERROR_ALREADY_EXISTS)return fail(L"Nao foi possivel criar a pasta de dados.");
 if(!CreateDirectoryW(bin,NULL)&&GetLastError()!=ERROR_ALREADY_EXISTS)return fail(L"Nao foi possivel criar a pasta do programa.");
 if(!hash_file(target)){
  swprintf(name,128,L"preparando_%lu.tmp",GetCurrentProcessId());if(!join_path(temp,32768,bin,name))return fail(L"Caminho muito longo.");
  HANDLE out=CreateFileW(temp,GENERIC_WRITE,0,NULL,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,NULL);if(out==INVALID_HANDLE_VALUE)return fail(L"Nao foi possivel preparar o programa. Feche a outra instancia e tente novamente.");
  unsigned char buffer[BUF];int success=1;
  for(int i=1;i<=6&&success;i++){
   swprintf(name,128,L"shield.part%02d",i);if(!join_path(part,32768,parts,name)){success=0;break;}
   HANDLE in=CreateFileW(part,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
   if(in==INVALID_HANDLE_VALUE){success=0;break;}
   DWORD got=0,written=0;
   while(1){if(!ReadFile(in,buffer,BUF,&got,NULL)){success=0;break;}if(!got)break;if(!WriteFile(out,buffer,got,&written,NULL)||written!=got){success=0;break;}}
   CloseHandle(in);
  }
  FlushFileBuffers(out);CloseHandle(out);
  if(!success||!hash_file(temp)){DeleteFileW(temp);return fail(L"O pacote esta incompleto ou corrompido. Extraia TODO o ZIP e mantenha a pasta dados_programa junto deste EXE.");}
  if(!MoveFileExW(temp,target,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)){DeleteFileW(temp);return fail(L"Nao foi possivel salvar o programa. Feche a instancia que esta aberta e tente novamente.");}
 }
 if(swprintf(command,32768,L"\"%ls\"",target)<=0)return fail(L"Caminho muito longo.");
 STARTUPINFOW si;PROCESS_INFORMATION pi;ZeroMemory(&si,sizeof(si));ZeroMemory(&pi,sizeof(pi));si.cb=sizeof(si);
 if(!CreateProcessW(target,command,NULL,NULL,FALSE,0,NULL,bin,&si,&pi))return fail(L"O Windows nao conseguiu iniciar o programa.");
 CloseHandle(pi.hThread);CloseHandle(pi.hProcess);return 0;
}

import { redirect } from 'next/navigation';

// Public landing → 종합 대시보드로 리디렉트.
// 데이터 입력·관리 기능은 /admin (관리자 인증 필요).
export default function Home() {
  redirect('/dashboard');
}

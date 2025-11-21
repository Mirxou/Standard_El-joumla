import React from "react";

export const metadata = {
  title: "Terms of Service | Wholesale AI Chatbot",
};

export default function TermsPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-10 space-y-6">
      <h1 className="text-2xl font-semibold">Terms of Service / الشروط والأحكام</h1>
      <section className="space-y-3 text-sm leading-relaxed">
        <p>
          <strong>English:</strong> By using the chat you agree to these terms. The
          service provides AI generated responses which may be inaccurate; do not
          rely on them for legal, financial, medical or investment decisions.
        </p>
        <p>
          <strong>العربية:</strong> باستخدامك للدردشة فإنك توافق على هذه الشروط. يقدم النظام
          ردوداً يتم توليدها آلياً وقد تكون غير دقيقة؛ لا تعتمد عليها في قرارات
          قانونية أو مالية أو طبية أو استثمارية.
        </p>
        <p>
          <strong>Acceptable Use / الاستخدام المقبول:</strong> You will not attempt to abuse,
          attack, scrape, reverse engineer or overload the service. Content that is
          illegal, hateful or violates Pi Network policies is prohibited.
        </p>
        <p>
          <strong>حسابك:</strong> المصادقة تتم عبر Pi Network. أنت مسؤول عن سرية وصولك.
        </p>
        <p>
          <strong>Data / البيانات:</strong> Messages are processed to generate responses; see
          privacy policy for details. We may temporarily cache content. You can
          request deletion via support.
        </p>
        <p>
          <strong>Disclaimer / إخلاء مسؤولية:</strong> Service provided "as is" without
          warranties. We are not liable for losses arising from use of generated
          content.
        </p>
        <p>
          <strong>Changes / التغييرات:</strong> We may modify these terms; continued use after
          changes means acceptance.
        </p>
        <p>
          <strong>Termination / الإنهاء:</strong> We may suspend access for violation of these
          terms or misuse.
        </p>
        <p>
          <strong>Contact / التواصل:</strong> For questions email: example@yourapp.com
        </p>
      </section>
    </main>
  );
}

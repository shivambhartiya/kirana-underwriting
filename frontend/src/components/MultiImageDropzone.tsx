import { useMemo, type ChangeEvent } from "react";

type Props = {
  files: { file: File; role: string }[];
  onChange: (files: { file: File; role: string }[]) => void;
  suggestions?: { filename: string; suggested_role: string; confidence: number; reason: string }[];
};

const defaultRoles = ["interior_shelf", "counter", "storefront", "street_view", "extra"];
const prettifyRole = (role: string) => role.split("_").join(" ");

export function MultiImageDropzone({ files, onChange, suggestions = [] }: Props) {
  const remaining = useMemo(() => 5 - files.length, [files.length]);

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    const chosen = Array.from(event.target.files || []).slice(0, remaining).map((file, index) => ({
      file,
      role: defaultRoles[Math.min(files.length + index, defaultRoles.length - 1)],
    }));
    onChange([...files, ...chosen]);
  }

  function setRole(index: number, role: string) {
    onChange(files.map((item, itemIndex) => (itemIndex === index ? { ...item, role } : item)));
  }

  return (
    <div className="panel p-6">
      <div className="rounded-3xl border border-dashed border-ink/20 bg-clay/20 p-8 text-center">
        <p className="text-lg font-semibold">Upload 3-5 store images</p>
        <p className="mt-2 text-sm text-ink/70">Cover shelves, counter, storefront, and street surroundings.</p>
        <input className="mt-4" type="file" accept="image/*" multiple onChange={handleFiles} />
      </div>
      <div className="mt-6 space-y-3">
        {files.map((item, index) => (
          <div key={`${item.file.name}-${index}`} className="flex items-center justify-between rounded-2xl border border-ink/10 bg-white px-4 py-3">
            <div>
              <p className="font-medium">{item.file.name}</p>
              <p className="text-xs text-ink/60">{Math.round(item.file.size / 1024)} KB</p>
              {suggestions.find((suggestion) => suggestion.filename === item.file.name) && (
                <p className="mt-1 text-xs text-pine">
                  Suggested: {prettifyRole(suggestions.find((suggestion) => suggestion.filename === item.file.name)?.suggested_role || "")}
                </p>
              )}
            </div>
            <select className="input max-w-44" value={item.role} onChange={(event) => setRole(index, event.target.value)}>
              {defaultRoles.map((role) => <option key={role} value={role}>{role}</option>)}
            </select>
          </div>
        ))}
      </div>
    </div>
  );
}
